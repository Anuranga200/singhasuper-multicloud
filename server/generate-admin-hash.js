import bcrypt from 'bcryptjs';

const password = process.argv[2] || 'Admin@123';

console.log('\n🔐 Generating bcrypt hash...\n');
console.log('Plain password:', password);

bcrypt.hash(password, 10, (err, hash) => {
  if (err) {
    console.error('❌ Error:', err);
    process.exit(1);
  }
  
  console.log('Hashed password:', hash);
  console.log('\n📋 SQL Command to update admin:\n');
  console.log(`UPDATE admins SET password_hash = '${hash}' WHERE email = 'admin@singha.com';`);
  console.log('\n✅ Copy the SQL command above and run it in MySQL!\n');
});
