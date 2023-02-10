from peewee import *

conn = SqliteDatabase('dish.db')

class BaseModel(Model):
    class Meta:
        database = conn

class Dish(BaseModel):
    # модель блюда или напитка
    dish_id = AutoField(column_name='DishId')
    name = TextField(column_name='Name')
    price = FloatField(column_name='Price')

class Ingredient(BaseModel):
    # модель ингридиентов
    ingredient_id = AutoField(column_name='IngredId')
    name = TextField(column_name='Name')
    measure = TextField(column_name='Measure')
    price = FloatField(column_name='Price')

class IngredientDish(BaseModel):
    # manytomany model 
    ingredient = ForeignKeyField(model=Ingredient)
    dish = ForeignKeyField(model=Dish)
    count = IntegerField(column_name='Count')
    
    class Meta:
        primary_key = CompositeKey('ingredient', 'dish')

def connect():
    conn.connect()
    try:
        conn.create_tables([Dish, Ingredient, IngredientDish])
    except:
        pass
if __name__ == '__main__':
    connect()
