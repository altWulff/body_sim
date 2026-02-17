#!/usr/bin/env python3
"""
Отдельный запуск боевой системы body_sim
Импортирует существующие классы тел и создает бойцов
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем существующие классы
try:
    from body_sim.body import MaleBody, FemaleBody, FutanariBody
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что body.py и names.py находятся в корне проекта")
    sys.exit(1)

from combat.core import Combatant
from combat.manager import CombatManager
from combat.commands import CombatConsole

def create_alex() -> Combatant:
    """Создает бойца Alex на основе MaleBody"""
    body = MaleBody()
    # Настраиваем для боя
    if hasattr(body, 'penises') and body.penises:
        p = body.penises[0]
        if hasattr(p, 'fluid_storage'):
            p.fluid_storage.current_volume = 100  # Запас спермы
    
    if hasattr(body, 'testicles') and body.testicles:
        for t in body.testicles:
            if hasattr(t, 'sperm_production'):
                t.sperm_production = 10
    
    return Combatant(body, "Alex")

def create_roxy() -> Combatant:
    """Создает бойца Roxy на основе FutanariBody"""
    body = FutanariBody()
    
    # Настраиваем грудь для молочной атаки
    if hasattr(body, 'breasts') and body.breasts:
        for b in body.breasts:
            if hasattr(b, 'volume'):
                b.volume = 1500  # Большой объем для Breast Crush
            if hasattr(b, 'lactation_system'):
                b.lactation_system.state = "ACTIVE"
                if hasattr(b.lactation_system, 'milk_storage'):
                    b.lactation_system.milk_storage = 1000
    
    # Настраиваем матку
    if hasattr(body, 'uterus'):
        u = body.uterus
        if hasattr(u, 'volume'):
            u.volume = 500
        if hasattr(u, 'max_volume'):
            u.max_volume = 5000
    
    # Пенис для Roxy
    if hasattr(body, 'penises') and body.penises:
        p = body.penises[0]
        if hasattr(p, 'fluid_storage'):
            p.fluid_storage.current_volume = 50
    
    return Combatant(body, "Roxy Migurdia")

def create_random_fighter(name: str, sex: str = "female") -> Combatant:
    """Создает случайного бойца"""
    if sex == "male":
        body = MaleBody()
    elif sex == "futanari":
        body = FutanariBody()
    else:
        body = FemaleBody()
    
    return Combatant(body, name)

def main():
    print("=== BodySim Combat Arena ===")
    print("1. Alex vs Roxy (Демо)")
    print("2. Создать своих бойцов")
    print("3. Быстрый бой (2 случайных)")
    
    choice = input("Выбор: ").strip()
    
    manager = CombatManager()
    
    if choice == "1":
        alex = create_alex()
        roxy = create_roxy()
        
        manager.add_combatant(alex, "Team A")
        manager.add_combatant(roxy, "Team B")
        
    elif choice == "2":
        print("\nСоздание бойца 1:")
        name1 = input("Имя: ") or "Fighter1"
        sex1 = input("Пол (male/female/futanari): ") or "female"
        c1 = create_random_fighter(name1, sex1)
        manager.add_combatant(c1, "A")
        
        print("\nСоздание бойца 2:")
        name2 = input("Имя: ") or "Fighter2"
        sex2 = input("Пол (male/female/futanari): ") or "female"
        c2 = create_random_fighter(name2, sex2)
        manager.add_combatant(c2, "B")
        
    elif choice == "3":
        c1 = create_random_fighter("Alpha", "futanari")
        c2 = create_random_fighter("Beta", "male")
        manager.add_combatant(c1, "A")
        manager.add_combatant(c2, "B")
    else:
        print("Неверный выбор")
        return
    
    # Запуск боя
    console = CombatConsole(manager)
    console.start()

if __name__ == "__main__":
    main()
