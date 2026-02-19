"""
Lambda function for rotating database credentials in AWS Secrets Manager
This function is triggered by EventBridge every 90 days
"""

import json
import boto3
import os
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client('secretsmanager')
rds_client = boto3.client('rds')


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for credential rotation
    
    Args:
        event: EventBridge event or Secrets Manager rotation event
        context: Lambda context
        
    Returns:
        Response dictionary with status
    """
    try:
        logger.info("Starting credential rotation")
        
        # Get the secret ARN from environment
        secret_arn = os.environ.get('DB_SECRET_ARN')
        if not secret_arn:
            raise ValueError("DB_SECRET_ARN environment variable not set")
        
        # Get current secret value
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        current_secret = json.loads(response['SecretString'])
        
        # Generate new password
        new_password_response = secrets_client.get_random_password(
            PasswordLength=32,
            ExcludeCharacters='/@"\'\\'
        )
        new_password = new_password_response['RandomPassword']
        
        # Update the secret with new password
        new_secret = current_secret.copy()
        new_secret['password'] = new_password
        
        secrets_client.put_secret_value(
            SecretId=secret_arn,
            SecretString=json.dumps(new_secret)
        )
        
        logger.info(f"Successfully rotated credentials for secret: {secret_arn}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Credential rotation completed successfully',
                'secret_arn': secret_arn
            })
        }
        
    except Exception as e:
        logger.error(f"Error rotating credentials: {str(e)}")
        raise


def create_secret(service: str, secret_dict: Dict[str, str]) -> None:
    """
    Helper function to create a new secret version
    
    Args:
        service: Service name
        secret_dict: Dictionary containing secret values
    """
    secrets_client.create_secret(
        Name=f"{service}-credentials",
        SecretString=json.dumps(secret_dict)
    )


def test_connection(host: str, port: int, username: str, password: str, database: str) -> bool:
    """
    Test database connection with new credentials
    
    Args:
        host: Database host
        port: Database port
        username: Database username
        password: Database password
        database: Database name
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        import pymysql
        
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            connect_timeout=5
        )
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False
