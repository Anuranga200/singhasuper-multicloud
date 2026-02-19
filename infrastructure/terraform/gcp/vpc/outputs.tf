# Outputs for GCP VPC Module

output "network_id" {
  description = "ID of the VPC network"
  value       = google_compute_network.main.id
}

output "network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.main.name
}

output "network_self_link" {
  description = "Self link of the VPC network"
  value       = google_compute_network.main.self_link
}

output "public_subnet_id" {
  description = "ID of public subnet"
  value       = google_compute_subnetwork.public.id
}

output "private_app_subnet_id" {
  description = "ID of private app subnet"
  value       = google_compute_subnetwork.private_app.id
}

output "private_db_subnet_id" {
  description = "ID of private database subnet"
  value       = google_compute_subnetwork.private_db.id
}

output "private_app_subnet_name" {
  description = "Name of private app subnet"
  value       = google_compute_subnetwork.private_app.name
}

output "router_id" {
  description = "ID of Cloud Router"
  value       = google_compute_router.main.id
}

output "nat_id" {
  description = "ID of Cloud NAT"
  value       = google_compute_router_nat.main.id
}

output "private_vpc_connection" {
  description = "Private VPC connection for Cloud SQL"
  value       = google_service_networking_connection.private_vpc_connection.network
}
