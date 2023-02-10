from model import *

class Base():

    def dish(self, dish):
        try:
            return Dish.get(Dish.name==dish)
        except:
            return False
    def ingredient(self, ingredient):
        try:
            return Ingredient.get(Ingredient.name==ingredient)
        except:
            return False
    def ingredient_dish(self, dish):
        data = list()
        for ingredient in Ingredient.select(
            Ingredient.name,
            Ingredient.price,
            IngredientDish.count,
            Ingredient.measure    
            ).join(IngredientDish).where(IngredientDish.dish==self.dish(dish).dish_id):
            data.append((ingredient.name, ingredient.ingredientdish.count, ingredient.measure, ingredient.price))
        return data



class AddDish(Base):
    dish_id = 0
    price = 0
    def __init__(self, name):
        self.name = name

    def add_dish(self):
        dish =  Dish.create(
            name=self.name,
            price=self.price)
        self.dish_id = dish.dish_id
        return dish
        
    def add_ingredient(self, ingredient, count):
        return IngredientDish.create(
            dish=self.dish_id,
            ingredient=self.ingredient(ingredient).ingredient_id,
            count = count)


class DeleteDish(Base):
    def __init__(self, name):
        self.name = name

    def delete(self):
        IngredientDish.delete().where(IngredientDish.dish==self.dish(self.name).dish_id).execute()
        return Dish.delete().where(Dish.name==self.name).execute()


class InfoDish(Base):
    ''' класс сбора информации о блюде, вычисление себестоимости и маржинальности '''
    def __init__(self, name):
        self.name = name

    def cost_price(self):
        #себестоимость
        data = self.ingredient_dish(self.name)
        tot = 0
        for ingred in data:
            tot += ingred[1] * ingred[3]
        return tot
    def marge(self):
        # (цена продажи - себестоимость)/Цена продажи *100%
        return (self.dish(self.name).price - self.cost_price()) / self.dish(self.name).price * 100

def all_dish():
    return Dish.select()

def all_ingredient():
    return Ingredient.select()
