#!/usr/bin/env python3
"""Telegram Member Scraper & Adder - Licensed Version"""

import os
import sys
import pickle
import asyncio
import random
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass

from pyrogram import Client
from pyrogram.errors import (
    FloodWait,
    PeerFlood,
    UserPrivacyRestricted,
    ChatAdminRequired,
    UserAlreadyParticipant,
    UsernameNotOccupied,
    InviteHashInvalid,
    InviteHashExpired,
    PhoneNumberBanned,
    RPCError
)
from colorama import init, Fore

# Initialize colors
init(autoreset=True)

# Configuration
API_ID = 6627460
API_HASH = "27a53a0965e486a2bc1b1fcde473b1c4"
SESSIONS_DIR = Path("sessions")
ACCOUNTS_FILE = Path("vars.txt")
STATUS_FILE = Path("status.dat")
USAGE_FILE = Path(".usage_data.dat")

# SHA-256 Hash of your password. 
# Current Password: "MEMBER-PRO-2026"
ENCRYPTED_KEY_HASH = "7a40b39e6a98f4863f619e830f898305c6d36e86427382d56a76059d6092040b"

SESSIONS_DIR.mkdir(exist_ok=True)

class Color:
    R = Fore.RED
    LG = Fore.LIGHTGREEN_EX
    RS = Fore.RESET
    W = Fore.WHITE
    CY = Fore.CYAN
    Y = Fore.YELLOW

@dataclass
class Account:
    phone: str
    
    @property
    def session_name(self) -> str:
        return str(SESSIONS_DIR / self.phone)

# --- License Logic ---
def check_license():
    usage_count = 0
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, 'rb') as f:
                usage_count = pickle.load(f)
        except:
            usage_count = 0

    if usage_count >= 2:
        print(f"{Color.Y}[!] Trial period ended. License Key required.{Color.RS}")
        user_input = input(f"{Color.CY}Enter Password: {Color.RS}").strip()
        
        # Hash user input to compare with stored hash
        input_hash = hashlib.sha256(user_input.encode()).hexdigest()
        
        if input_hash != ENCRYPTED_KEY_HASH:
            print(f"{Color.R}[!] Incorrect Password. Access Denied.{Color.RS}")
            sys.exit(1)
        else:
            print(f"{Color.LG}[+] Access Granted.{Color.RS}")
    
    return usage_count

def increment_usage(current_count):
    with open(USAGE_FILE, 'wb') as f:
        pickle.dump(current_count + 1, f)

@dataclass
class Progress:
    group_link: str
    index: int
    
    def save(self):
        with open(STATUS_FILE, 'wb') as f:
            pickle.dump([self.group_link, self.index], f)
    
    @classmethod
    def load(cls) -> Optional['Progress']:
        if not STATUS_FILE.exists(): 
            return None
        try:
            with open(STATUS_FILE, 'rb') as f:
                data = pickle.load(f)
                return cls(data[0], data[1])
        except Exception:
            return None

class MemberScraper:
    def __init__(self, account: Account):
        self.account = account
        self.client: Optional[Client] = None
    
    async def __aenter__(self):
        self.client = Client(
            name=self.account.session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            workdir=str(Path.cwd())
        )
        await self.client.start()
        return self
    
    async def __aexit__(self, *args):
        if self.client:
            await self.client.stop()
    
    async def resolve_chat(self, link: str):
        clean = link.replace('https://t.me/', '').replace('@', '').replace('joinchat/', '')
        return await self.client.get_chat(clean)

    async def join_group(self, group_link: str) -> bool:
        try:
            clean = group_link.replace('https://t.me/', '').replace('@', '')
            await self.client.join_chat(clean)
            return True
        except UserAlreadyParticipant:
            return True
        except Exception as e:
            print(f"{Color.R}[!] Join failed: {e}{Color.RS}")
            return False
    
    async def scrape_members(self, group_link: str, limit: int = 5000) -> List[Any]:
        print(f"{Color.W}[i] Scraping from {group_link}...{Color.RS}")
        members = []
        try:
            chat = await self.resolve_chat(group_link)
            async for member in self.client.get_chat_members(chat.id, limit=limit):
                if member.user and not member.user.is_bot and not member.user.is_deleted:
                    members.append(member.user)
            return members
        except Exception as e:
            print(f"{Color.R}[!] Scrape failed: {e}{Color.RS}")
            return []

    async def add_to_group(self, target_link: str, users: List[Any], delay: float = 2) -> Tuple[int, int, bool]:
        added, failed = 0, 0
        hit_flood = False
        try:
            target_chat = await self.resolve_chat(target_link)
            for user in users:
                try:
                    await self.client.add_chat_members(target_chat.id, user.id)
                    added += 1
                    print(f"{Color.LG}[+] Added {user.first_name or 'User'}{Color.RS}")
                    await asyncio.sleep(delay)
                except PeerFlood:
                    print(f"{Color.R}[!] Account limited. Switching...{Color.RS}")
                    hit_flood = True
                    break
                except (UserPrivacyRestricted, UserAlreadyParticipant):
                    failed += 1
                except FloodWait as e:
                    print(f"{Color.Y}[!] Waiting {e.value}s...{Color.RS}")
                    await asyncio.sleep(e.value)
                except Exception:
                    failed += 1
        except Exception as e:
            print(f"{Color.R}[!] Error: {e}{Color.RS}")
        
        return added, failed, hit_flood

class AccountManager:
    def __init__(self):
        self.accounts: List[Account] = []
        self._load_accounts()
    
    def _load_accounts(self):
        if not ACCOUNTS_FILE.exists():
            print(f"{Color.R}[!] {ACCOUNTS_FILE} not found!{Color.RS}")
            sys.exit(1)
        try:
            with open(ACCOUNTS_FILE, 'rb') as f:
                while True:
                    try:
                        data = pickle.load(f)
                        if data and isinstance(data, list):
                            self.accounts.append(Account(str(data[0])))
                    except EOFError:
                        break
        except Exception as e:
            print(f"Error loading accounts: {e}")

async def main():
    print(f"\n{Color.CY}Telegram Multi-Account Adder v2.0{Color.RS}")
    
    # 1. License Check
    current_usage = check_license()
    
    manager = AccountManager()
    if not manager.accounts:
        return

    progress = Progress.load()
    if progress:
        res = input(f"Resume {progress.group_link} at index {progress.index}? (y/n): ").lower()
        if res == 'y':
            group_link, start_index = progress.group_link, progress.index
        else:
            group_link, start_index = input("Source Group Link: "), 0
    else:
        group_link, start_index = input("Source Group Link: "), 0

    target_link = input("Target Group Link: ")
    num_to_use = int(input(f"Accounts to use (Max {len(manager.accounts)}): "))
    delay = float(input("Delay between adds (sec): "))

    async with MemberScraper(manager.accounts[0]) as scraper:
        await scraper.join_group(group_link)
        members = await scraper.scrape_members(group_link)

    if not members:
        print("No members found.")
        return

    current_idx = start_index
    total_added = 0

    for i in range(min(num_to_use, len(manager.accounts))):
        if current_idx >= len(members): break
        
        acc = manager.accounts[i]
        print(f"\n{Color.W}--- Using Account: {acc.phone} ---{Color.RS}")
        
        async with MemberScraper(acc) as scraper:
            await scraper.join_group(target_link)
            batch = members[current_idx : current_idx + 40]
            added, failed, flood = await scraper.add_to_group(target_link, batch, delay)
            
            total_added += added
            current_idx += (added + failed)
            Progress(group_link, current_idx).save()
            
            if flood: continue

    print(f"\n{Color.LG}Task Complete. Total added: {total_added}{Color.RS}")
    
    # 2. Update usage count if work was done
    if total_added > 0:
        increment_usage(current_usage)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Color.Y}Stopped.{Color.RS}")
    except Exception as e:
        print(f"\n{Color.R}Fatal error: {e}{Color.RS}")