#!/data/data/com.termux/files/usr/bin/bash

# Prevent Termux from sleeping
termux-wake-lock

clear
echo "Installing Shawshank..."

# 1. Update and install dependencies
pkg update -y
pkg install -y python git

# 2. Clone the repository
cd $HOME
# Remove folder if it exists to allow a fresh install
rm -rf Shawshank
git clone https://github.com/yonasazimeraw0/Shawshank

# 3. Enter the directory
cd Shawshank

# 4. Install requirements (fix typo)
if [ -f "requir.txt" ]; then
    pip install -r requirements.txt
fi

# Release wake lock
termux-wake-unlock

clear
echo "---------------------------------------"
echo "  Installation Complete!"
echo "  Run 'ls' to see your files."
echo "  Start with: python add.py"
echo "---------------------------------------"

# Add to bashrc only if not already there
if ! grep -q "cd ~/Shawshank" ~/.bashrc; then
    echo "cd ~/Shawshank" >> ~/.bashrc
fi

# This keeps the user inside the Shawshank folder after the script ends
exec bash
