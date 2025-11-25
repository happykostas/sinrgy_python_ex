from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from enum import Enum
import os


DEBUG = os.environ.get("DEBUG") == "1"


def debug_log(message: str):
    if DEBUG:
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[DEBUG {timestamp}] {message}")


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MATERIAL = "material"


class Item(ABC):
    def __init__(self, name: str, weight: float, cost: int, item_type: ItemType):
        self.name = name
        self.weight = weight
        self.cost = cost
        self.item_type = item_type
        debug_log(
            f"Item created: {name} (weight: {weight}, cost: {cost}, type: {item_type.value})"
        )

    @abstractmethod
    def use(self, character):
        pass

    def __repr__(self):
        return f"{self.name} ({self.item_type.value})"


class Weapon(Item):
    def __init__(
        self, name: str, weight: float, cost: int, damage: int, weapon_class: str
    ):
        super().__init__(name, weight, cost, ItemType.WEAPON)
        self.damage = damage
        self.weapon_class = weapon_class
        debug_log(f"Weapon created: {name}, damage: {damage}, class: {weapon_class}")

    def use(self, character):
        debug_log(f"Attempting to equip weapon {self.name} on {character.name}")
        if character.can_equip_weapon(self):
            character.equipment["weapon"] = self
            debug_log(f"Weapon {self.name} equipped successfully")
            return True
        debug_log(f"Cannot equip weapon {self.name} - class restriction")
        return False


class Armor(Item):
    def __init__(self, name: str, weight: float, cost: int, defense: int):
        super().__init__(name, weight, cost, ItemType.ARMOR)
        self.defense = defense
        debug_log(f"Armor created: {name}, defense: {defense}")

    def use(self, character):
        debug_log(f"Equipping armor {self.name} on {character.name}")
        character.equipment["armor"] = self
        return True


class Potion(Item):
    def __init__(self, name: str, weight: float, cost: int, effect: str, value: int):
        super().__init__(name, weight, cost, ItemType.CONSUMABLE)
        self.effect = effect
        self.value = value
        debug_log(f"Potion created: {name}, effect: {effect}, value: {value}")

    def use(self, character):
        debug_log(f"Using potion {self.name} on {character.name}")
        if self.effect == "heal":
            character.health = min(character.max_health, character.health + self.value)
            debug_log(
                f"{character.name} healed for {self.value} HP, current health: {character.health}"
            )
        character.inventory.remove_item(self)
        return True


class Material(Item):
    def __init__(self, name: str, weight: float, cost: int, material_type: str):
        super().__init__(name, weight, cost, ItemType.MATERIAL)
        self.material_type = material_type
        debug_log(f"Material created: {name}, type: {material_type}")

    def use(self, character):
        debug_log(f"Material {self.name} cannot be used directly")
        return False


class Inventory:
    def __init__(self, max_weight: float):
        self.max_weight = max_weight
        self.items: Dict[Item, int] = {}
        debug_log(f"Inventory created with max weight: {max_weight}")

    def add_item(self, item: Item, quantity: int = 1) -> bool:
        current_weight = self.calculate_weight(self.items)
        new_weight = current_weight + (item.weight * quantity)

        debug_log(
            f"Adding {quantity}x {item.name}, current: {current_weight}, new: {new_weight}, max: {self.max_weight}"
        )

        if new_weight > self.max_weight:
            debug_log(f"Cannot add item - exceeds max weight")
            return False

        if item in self.items:
            self.items[item] += quantity
        else:
            self.items[item] = quantity

        debug_log(f"Item added successfully, now have {self.items[item]}x {item.name}")
        return True

    def remove_item(self, item: Item, quantity: int = 1) -> bool:
        debug_log(f"Removing {quantity}x {item.name}")

        if item not in self.items or self.items[item] < quantity:
            debug_log(f"Cannot remove item - insufficient quantity")
            return False

        self.items[item] -= quantity
        if self.items[item] == 0:
            del self.items[item]
            debug_log(f"Item removed completely from inventory")
        else:
            debug_log(f"Removed {quantity}x, {self.items[item]}x remaining")

        return True

    @staticmethod
    def calculate_weight(items: Dict[Item, int]) -> float:
        weight = sum(item.weight * quantity for item, quantity in items.items())
        debug_log(f"Calculated total weight: {weight}")
        return weight

    @classmethod
    def create_starter_inventory(cls):
        debug_log("Creating starter inventory")
        inventory = cls(max_weight=50.0)

        water = Potion("Water", 0.5, 5, "heal", 10)
        bread = Potion("Bread", 0.3, 3, "heal", 15)
        gold = Material("Gold Coins", 0.1, 1, "currency")

        inventory.add_item(water, 2)
        inventory.add_item(bread, 3)
        inventory.add_item(gold, 50)

        debug_log("Starter inventory created")
        return inventory

    def get_item_by_name(self, name: str) -> Optional[Item]:
        for item in self.items:
            if item.name == name:
                return item
        return None


class Character(ABC):
    def __init__(self, name: str, health: int, max_weight: float):
        self.name = name
        self.health = health
        self.max_health = health
        self.inventory = Inventory(max_weight)
        self.equipment: Dict[str, Optional[Item]] = {"weapon": None, "armor": None}
        self.level = 1
        debug_log(
            f"Character created: {name} (health: {health}, class: {self.__class__.__name__})"
        )

    def pick_up_item(self, item: Item, quantity: int = 1) -> bool:
        debug_log(f"{self.name} attempting to pick up {quantity}x {item.name}")
        return self.inventory.add_item(item, quantity)

    def use_item(self, item_name: str) -> bool:
        debug_log(f"{self.name} attempting to use item: {item_name}")
        item = self.inventory.get_item_by_name(item_name)

        if not item:
            debug_log(f"Item {item_name} not found in inventory")
            return False

        return item.use(self)

    @abstractmethod
    def can_equip_weapon(self, weapon: Weapon) -> bool:
        pass

    @abstractmethod
    def get_item_bonus(self, item: Item) -> float:
        pass

    @classmethod
    def create_character(cls, character_class: str, name: str):
        debug_log(
            f"Creating character via factory: class={character_class}, name={name}"
        )

        classes = {"warrior": Warrior, "mage": Mage, "archer": Archer}

        if character_class.lower() not in classes:
            debug_log(f"Invalid character class: {character_class}")
            return None

        char_class = classes[character_class.lower()]
        character = char_class(name)
        character.inventory = Inventory.create_starter_inventory()

        debug_log(f"Character created successfully")
        return character


class Warrior(Character):
    def __init__(self, name: str):
        super().__init__(name, health=150, max_weight=80.0)
        self.allowed_weapons = ["sword", "axe", "mace"]
        debug_log(f"Warrior initialized, allowed weapons: {self.allowed_weapons}")

    def can_equip_weapon(self, weapon: Weapon) -> bool:
        can_equip = weapon.weapon_class in self.allowed_weapons
        debug_log(f"Warrior weapon check: {weapon.weapon_class} -> {can_equip}")
        return can_equip

    def get_item_bonus(self, item: Item) -> float:
        if isinstance(item, Weapon):
            bonus = 1.2
            debug_log(f"Warrior bonus for weapon: {bonus}x")
            return bonus
        return 1.0


class Mage(Character):
    def __init__(self, name: str):
        super().__init__(name, health=80, max_weight=40.0)
        self.allowed_weapons = ["staff", "wand"]
        debug_log(f"Mage initialized, allowed weapons: {self.allowed_weapons}")

    def can_equip_weapon(self, weapon: Weapon) -> bool:
        can_equip = weapon.weapon_class in self.allowed_weapons
        debug_log(f"Mage weapon check: {weapon.weapon_class} -> {can_equip}")
        return can_equip

    def get_item_bonus(self, item: Item) -> float:
        if isinstance(item, Potion):
            bonus = 1.5
            debug_log(f"Mage bonus for potion: {bonus}x")
            return bonus
        return 1.0


class Archer(Character):
    def __init__(self, name: str):
        super().__init__(name, health=100, max_weight=60.0)
        self.allowed_weapons = ["bow", "crossbow"]
        debug_log(f"Archer initialized, allowed weapons: {self.allowed_weapons}")

    def can_equip_weapon(self, weapon: Weapon) -> bool:
        can_equip = weapon.weapon_class in self.allowed_weapons
        debug_log(f"Archer weapon check: {weapon.weapon_class} -> {can_equip}")
        return can_equip

    def get_item_bonus(self, item: Item) -> float:
        if isinstance(item, Armor) and item.weight < 10:
            bonus = 1.3
            debug_log(f"Archer bonus for light armor: {bonus}x")
            return bonus
        return 1.0


class Recipe:
    def __init__(
        self, name: str, required_level: int, ingredients: Dict[str, int], result: Item
    ):
        self.name = name
        self.required_level = required_level
        self.ingredients = ingredients
        self.result = result
        debug_log(f"Recipe created: {name}, required level: {required_level}")


class CraftingSystem:
    _recipes: List[Recipe] = []

    @classmethod
    def initialize_recipes(cls):
        debug_log("Initializing crafting recipes")

        iron_sword = Weapon("Iron Sword", 5.0, 100, 25, "sword")
        wooden_staff = Weapon("Wooden Staff", 3.0, 80, 20, "staff")
        leather_armor = Armor("Leather Armor", 8.0, 120, 15)

        cls._recipes = [
            Recipe("Iron Sword", 1, {"Iron Ore": 3, "Wood": 1}, iron_sword),
            Recipe("Wooden Staff", 1, {"Wood": 2, "Crystal": 1}, wooden_staff),
            Recipe("Leather Armor", 2, {"Leather": 4, "Thread": 2}, leather_armor),
        ]

        debug_log(f"Initialized {len(cls._recipes)} recipes")

    @staticmethod
    def available_recipes(character_level: int) -> List[Recipe]:
        debug_log(f"Finding recipes for level {character_level}")
        available = [
            recipe
            for recipe in CraftingSystem._recipes
            if recipe.required_level <= character_level
        ]
        debug_log(f"Found {len(available)} available recipes")
        return available

    @classmethod
    def craft_item(cls, recipe: Recipe, character: Character) -> Optional[Item]:
        debug_log(f"Attempting to craft: {recipe.name}")

        if character.level < recipe.required_level:
            debug_log(
                f"Character level too low: {character.level} < {recipe.required_level}"
            )
            return None

        for ingredient_name, required_quantity in recipe.ingredients.items():
            item = character.inventory.get_item_by_name(ingredient_name)
            if not item or character.inventory.items[item] < required_quantity:
                debug_log(
                    f"Missing ingredient: {ingredient_name} (need {required_quantity})"
                )
                return None

        debug_log(f"All ingredients available, crafting {recipe.name}")

        for ingredient_name, required_quantity in recipe.ingredients.items():
            item = character.inventory.get_item_by_name(ingredient_name)
            character.inventory.remove_item(item, required_quantity)

        character.inventory.add_item(recipe.result)
        debug_log(f"Crafted {recipe.name} successfully")
        return recipe.result

    @classmethod
    def dismantle_item(cls, item: Item) -> Dict[str, int]:
        debug_log(f"Dismantling item: {item.name}")

        materials = {}

        if isinstance(item, Weapon):
            if item.weapon_class in ["sword", "axe"]:
                materials["Iron Ore"] = 2
                materials["Wood"] = 1
            elif item.weapon_class in ["staff", "wand"]:
                materials["Wood"] = 2
        elif isinstance(item, Armor):
            materials["Leather"] = 2
            materials["Thread"] = 1

        debug_log(f"Dismantled into: {materials}")
        return materials


if __name__ == "__main__":
    debug_log("===================== START =====================")

    CraftingSystem.initialize_recipes()

    warrior = Character.create_character("warrior", "Aragorn")
    mage = Character.create_character("mage", "Gandalf")
    archer = Character.create_character("archer", "Legolas")

    sword = Weapon("Steel Sword", 6.0, 150, 30, "sword")
    staff = Weapon("Magic Staff", 4.0, 200, 35, "staff")
    bow = Weapon("Longbow", 3.0, 120, 28, "bow")
    armor = Armor("Chain Mail", 15.0, 180, 25)
    health_potion = Potion("Health Potion", 0.5, 50, "heal", 50)

    print(f"\n=== Testing {warrior.name} (Warrior) ===")
    warrior.pick_up_item(sword)
    warrior.pick_up_item(health_potion, 3)
    warrior.use_item("Steel Sword")
    print(f"Equipped weapon: {warrior.equipment['weapon']}")

    print(f"\n=== Testing {mage.name} (Mage) ===")
    mage.pick_up_item(staff)
    mage.pick_up_item(sword)
    mage.use_item("Magic Staff")
    mage.use_item("Steel Sword")
    print(f"Equipped weapon: {mage.equipment['weapon']}")

    print(f"\n=== Testing {archer.name} (Archer) ===")
    archer.pick_up_item(bow)
    archer.pick_up_item(armor)
    archer.use_item("Longbow")
    archer.use_item("Chain Mail")
    print(f"Equipped weapon: {archer.equipment['weapon']}")
    print(f"Equipped armor: {archer.equipment['armor']}")

    print(f"\n=== Inventory Weight Test ===")
    print(
        f"Current weight: {Inventory.calculate_weight(warrior.inventory.items):.1f}/{warrior.inventory.max_weight}"
    )

    print(f"\n=== Crafting System Test ===")
    iron_ore = Material("Iron Ore", 2.0, 10, "metal")
    wood = Material("Wood", 1.0, 5, "wood")

    test_char = Character.create_character("warrior", "Smith")
    test_char.pick_up_item(iron_ore, 5)
    test_char.pick_up_item(wood, 3)

    available = CraftingSystem.available_recipes(test_char.level)
    print(f"Available recipes: {len(available)}")

    if available:
        crafted = CraftingSystem.craft_item(available[0], test_char)
        print(f"Crafted: {crafted}")

    print(f"\n=== Dismantle Test ===")
    materials = CraftingSystem.dismantle_item(sword)
    print(f"Dismantled {sword.name} into: {materials}")

    debug_log("===================== END ========================")
