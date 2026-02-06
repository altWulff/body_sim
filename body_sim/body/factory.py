# body_sim/body/factory.py
"""
Фабрика для создания тел.
"""

from body_sim.body.body import MaleBody, FemaleBody, FutanariBody, Body
from body_sim.core.enums import BodyType, TesticleSize, Sex


class BodyFactory:
    @staticmethod
    def create_male(
        name: str = "Male",
        body_type: BodyType = BodyType.AVERAGE,
        penis_count: int = 1,
        penis_size: float = 15.0,
        testicle_size: TesticleSize = TesticleSize.AVERAGE
    ) -> MaleBody:
        return MaleBody(
            name=name,
            body_type=body_type,
            penis_count=penis_count,
            penis_size=penis_size,
            testicle_size=testicle_size
        )
    
    @staticmethod
    def create_female(
        name: str = "Female",
        body_type: BodyType = BodyType.CURVY,
        vagina_count: int = 1,
        clitoris_count: int = 1,
        breast_cup: str = "C",
        breast_count: int = 2,
        vagina_depth: float = 10.0,
        vagina_width: float = 3.0,
        clitoris_size: float = 1.5
    ) -> FemaleBody:
        return FemaleBody(
            name=name,
            body_type=body_type,
            vagina_count=vagina_count,
            clitoris_count=clitoris_count,
            breast_cup=breast_cup,
            breast_count=breast_count,
            vagina_depth=vagina_depth,
            vagina_width=vagina_width,
            clitoris_size=clitoris_size
        )
    
    @staticmethod
    def create_futanari(
        name: str = "Futanari",
        body_type: BodyType = BodyType.CURVY,
        penis_count: int = 1,
        penis_size: float = 18.0,
        has_scrotum: bool = True,
        testicle_size: TesticleSize = TesticleSize.LARGE,
        internal_testicles: bool = False,
        vagina_count: int = 1,
        clitoris_count: int = 1,
        breast_cup: str = "E",
        breast_count: int = 2
    ) -> FutanariBody:
        return FutanariBody(
            name=name,
            body_type=body_type,
            penis_count=penis_count,
            penis_size=penis_size,
            has_scrotum=has_scrotum,
            testicle_size=testicle_size,
            internal_testicles=internal_testicles,
            vagina_count=vagina_count,
            clitoris_count=clitoris_count,
            breast_cup=breast_cup,
            breast_count=breast_count
        )
    
    @staticmethod
    def quick_create(sex_type: str, name: str = "Player") -> Body:
        """Быстрое создание по строковому типу."""
        sex_map = {
            'male': (Sex.MALE, BodyFactory.create_male),
            'female': (Sex.FEMALE, BodyFactory.create_female),
            'futa': (Sex.FUTANARI, BodyFactory.create_futanari),
            'futanari': (Sex.FUTANARI, BodyFactory.create_futanari),
        }
        
        sex_type = sex_type.lower()
        if sex_type not in sex_map:
            raise ValueError(f"Unknown sex type: {sex_type}. Use: male, female, futa")
        
        _, factory_func = sex_map[sex_type]
        return factory_func(name=name)
        