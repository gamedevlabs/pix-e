// install.js
const { execSync } = require('child_process');
const { existsSync } = require('fs');
const path = require('path');

// Paths
const backendDir = path.join(__dirname, 'backend');
const frontendDir = path.join(__dirname, 'frontend');
const venvDir = path.join(backendDir, '.venv');

// Helper to run commands
function runCommand(command, options = {}) {
  console.log(`Running: ${command}`);
  execSync(command, { stdio: 'inherit', ...options });
}

async function main() {
  console.log('🚀 Starting monorepo install script...\n');

  // Step 1: Setup Python virtualenv if not exists
  if (!existsSync(venvDir)) {
    console.log('🔧 Creating Python virtual environment...');
    runCommand(`python -m venv .venv`, { cwd: backendDir });
  } else {
    console.log('✅ Python virtual environment already exists.');
  }

  // Step 2: Install backend dependencies
  console.log('\n📦 Installing backend (Django) dependencies...');
  const activateCmd = process.platform === 'win32'
    ? `.\\.venv\\Scripts\\activate && pip install -r requirements.txt`
    : `source ./.venv/bin/activate && pip install -r requirements.txt`;
  runCommand(activateCmd, { cwd: backendDir, shell: true });

  // Step 2.5: Run migrations
  console.log('\n📦 Installing backend (Django) dependencies...');
  const runmigration = "(.venv\\Scripts\\python.exe manage.py migrate || ./.venv/bin/python manage.py migrate)";
  runCommand(runmigration, { cwd: backendDir, shell: true });

  // Step 3: Install frontend dependencies
  console.log('\n📦 Installing frontend (Nuxt) dependencies...');
  runCommand(`npm install`, { cwd: frontendDir });

  // Step 4: Install project root dependencies
  console.log('\n📦 Installing project root dependencies...');
  runCommand(`npm install`);

  console.log('\n🎉 All dependencies installed successfully!');
}

main().catch((error) => {
  console.error('❌ Installation failed:', error);
  process.exit(1);
});
