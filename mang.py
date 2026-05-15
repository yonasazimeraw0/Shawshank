#!/usr/bin/env python3

import os
import sys
import pickle
import asyncio
import random
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager

from pyrogram import Client
from pyrogram.errors import PhoneNumberBanned, FloodWait, SessionPasswordNeeded
from colorama import init, Fore

init(autoreset=True)

API_ID = 6627460
API_HASH = "27a53a0965e486a2bc1b1fcde473b1c4"
SESSIONS_DIR = Path("sessions")
ACCOUNTS_FILE = Path("vars.txt")

SESSIONS_DIR.mkdir(exist_ok=True)

class Style:
    SUCCESS = Fore.LIGHTGREEN_EX
    ERROR = Fore.RED
    INFO = Fore.CYAN
    WARNING = Fore.YELLOW
    RESET = Fore.RESET
    BOLD = "\033[1m"

def get_random_device():
    devices = [
        {"model": "Tecno Spark 10 Pro", "sys": "Android 13"},
        {"model": "Tecno Camon 20", "sys": "Android 13"},
        {"model": "Infinix Hot 30", "sys": "Android 12"},
        {"model": "Infinix Note 30", "sys": "Android 13"},
        {"model": "Samsung Galaxy A14", "sys": "Android 13"},
        {"model": "Samsung Galaxy A04s", "sys": "Android 12"},
        {"model": "Itel S23", "sys": "Android 12"},
        {"model": "Xiaomi Redmi 12C", "sys": "Android 12"},
        {"model": "Oppo A17", "sys": "Android 12"},
        {"model": "Vivo Y16", "sys": "Android 12"}
    ]
    device = random.choice(devices)
    app_version = f"{random.randint(9, 10)}.{random.randint(0, 9)}.{random.randint(0, 5)}"
    return device["model"], device["sys"], app_version

@dataclass
class Account:
    phone: str
    
    @property
    def session_path(self) -> Path:
        return SESSIONS_DIR / f"{self.phone}.session"
    
    @property
    def exists(self) -> bool:
        return self.session_path.exists()

class AccountManager:
    def __init__(self, accounts_file: Path = ACCOUNTS_FILE):
        self.accounts_file = accounts_file
        self._accounts: List[Account] = []
        self._load_accounts()
    
    def _load_accounts(self) -> None:
        if not self.accounts_file.exists() or self.accounts_file.stat().st_size == 0:
            return
        try:
            with open(self.accounts_file, 'rb') as f:
                while True:
                    try:
                        data = pickle.load(f)
                        if isinstance(data, list) and data:
                            self._accounts.append(Account(phone=str(data[0])))
                    except EOFError: break
        except Exception as e:
            print(f"{Style.ERROR}Error loading accounts: {e}")
    
    def _save_accounts(self) -> None:
        with open(self.accounts_file, 'wb') as f:
            for account in self._accounts:
                pickle.dump([account.phone], f)

    def add_accounts(self, phones: List[str]) -> List[Account]:
        new_accounts = [Account(phone=p) for p in phones]
        self._accounts.extend(new_accounts)
        self._save_accounts()
        return new_accounts

    def delete_account(self, phone: str) -> bool:
        account_to_remove = None
        for account in self._accounts:
            if account.phone == phone:
                account_to_remove = account
                break
        
        if account_to_remove:
            self._accounts.remove(account_to_remove)
            self._save_accounts()
            
            if account_to_remove.exists:
                try:
                    account_to_remove.session_path.unlink()
                except Exception as e:
                    print(f"{Style.WARNING}⚠️ Removed from list, but failed to delete file: {e}")
            return True
        return False

@asynccontextmanager
async def telegram_session(phone: str):
    model, sys_ver, app_ver = get_random_device()
    client = Client(
        name=phone,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=str(SESSIONS_DIR),
        device_model=model,
        system_version=sys_ver,
        app_version=app_ver
    )
    try:
        await client.start()
        yield client
    finally:
        await client.stop()

async def create_session(account: Account) -> bool:
    model, sys_ver, app_ver = get_random_device()
    print(f"{Style.INFO}Creating session as: {Style.BOLD}{model} ({sys_ver}){Style.RESET}")
    
    client = Client(
        name=account.phone,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=str(SESSIONS_DIR),
        phone_number=account.phone,
        device_model=model,
        system_version=sys_ver,
        app_version=app_ver
    )
    try:
        await client.start()
        print(f"{Style.SUCCESS}✅ Successfully logged in {account.phone}")
        await client.stop()
        return True
    except Exception as e:
        print(f"{Style.ERROR}❌ Failed {account.phone}: {e}")
        return False

async def main():
    manager = AccountManager()
    while True:
        print(f"\n{Style.INFO}--- Account Manager  ---")
        print("1. Add accounts\n2. Display all\n3. Delete account\n4. Quit")
        choice = input(f"\n{Style.BOLD}🎯 Choice: {Style.RESET}")

        if choice == '1':
            try:
                num = int(input("How many? "))
                for i in range(num):
                    phone = input(f"Phone {i+1}: ").strip().replace(" ", "")
                    acc = manager.add_accounts([phone])[0]
                    await create_session(acc)
            except Exception as e: print(e)
        elif choice == '2':
            print(f"\nTotal: {len(manager._accounts)}")
            for a in manager._accounts: print(f"- {a.phone} ({'Exists' if a.exists else 'No Session'})")
        elif choice == '3':
            if not manager._accounts:
                print(f"{Style.WARNING}No accounts available to delete.")
                continue
            
            print(f"\n{Style.INFO}Available accounts:")
            for idx, a in enumerate(manager._accounts, start=1):
                print(f"{idx}. {a.phone}")
                
            try:
                target_idx = int(input(f"\nSelect account index to delete (1-{len(manager._accounts)}): ")) - 1
                if 0 <= target_idx < len(manager._accounts):
                    target_phone = manager._accounts[target_idx].phone
                    confirm = 'y'
                    if confirm == 'y':
                        if manager.delete_account(target_phone):
                            print(f"{Style.SUCCESS}🗑️ Successfully deleted {target_phone} and its session.")
                        else:
                            print(f"{Style.ERROR}❌ Failed to delete account.")
                else:
                    print(f"{Style.ERROR}Invalid selection.")
            except ValueError:
                print(f"{Style.ERROR}Please enter a valid number.")
        elif choice == '4':
            break

if __name__ == "__main__":
    asyncio.run(main())
