# body_sim/__main__.py
"""
Точка входа: python -m body_sim
"""

import sys
from body_sim.ui.console import run_console
from body_sim.body.factory import BodyFactory
from body_sim.systems.events import EventfulBody
from body_sim.characters.roxy_migurdia import RoxyMigurdia

def create_demo_bodies():
    """Создание демонстрационных тел."""
    from body_sim.core.enums import BodyType, TesticleSize, FluidType
    
    bodies = []
    
    # Мужчина
    male = BodyFactory.create_male(
        name="Alex",
        body_type=BodyType.MUSCULAR,
        penis_size=16.0,
        testicle_size=TesticleSize.LARGE
    )
    male.scrotums[0].add_testicle_fluid_production(0, FluidType.CUM, 0.05)
    bodies.append(EventfulBody(male))
    
    # Женщина
    female = BodyFactory.create_female(
        name="Maria",
        body_type=BodyType.CURVY,
        breast_cup="D",
        vagina_depth=11.0
    )
    bodies.append(EventfulBody(female))
    
    # Футанари
    futa = BodyFactory.create_futanari(
        name="Rin",
        body_type=BodyType.AMAZON,
        breast_cup="F",
        penis_size=20.0,
        has_scrotum=True,
        internal_testicles=True
    )
    bodies.append(EventfulBody(futa))
    
    #create Roxy
    roxy = RoxyMigurdia()
    bodies.append(EventfulBody(roxy))
    
    return bodies

def main():
    """Главная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Breast & Body Simulation")
    parser.add_argument("--demo", "-d", action="store_true", help="Run demo")
    parser.add_argument("--create", "-c", choices=['male', 'female', 'futa'])
    
    args = parser.parse_args()
    
    if args.create:
        bodies = [BodyFactory.quick_create(args.create)]
    else:
        bodies = create_demo_bodies()
    
    print(f"Created {len(bodies)} bodies")
    
    if args.demo:
        from body_sim.ui.demo import run_demo
        run_demo(bodies)
    
    run_console(bodies)

if __name__ == "__main__":
    main()
