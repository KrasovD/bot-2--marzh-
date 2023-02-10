import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

import config
import base

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
data_ingr = list()
dish = base.AddDish('None')


@dp.message_handler(commands=['start'])
async def show_hello(message: types.Message):
    '''
    Сообщение при старте бота
    '''
    await message.answer(text='Привет, %s! Введите назвние блюда' % message.chat.first_name)

@dp.message_handler(commands=['all_dish'])
async def show_all_dish(message: types.Message):
    '''
    Вывод всех блюд списком
    '''
    text = ''
    for dish in base.all_dish():
        text += '{}\n'.format(dish.name)
    await message.answer(text = text)
@dp.message_handler(commands=['all_ingredient'])
async def show_all_dish(message: types.Message):
    '''
    Вывод всех ингридиентов
    '''
    text = ''
    for ingredient in base.all_ingredient():
        text += '{}\n'.format(ingredient.name)
    await message.answer(text = text)

@dp.message_handler(content_types=types.ContentType.TEXT)
async def message(message: types.Message):
    '''
    Перехват сообщения и поиск в БД
    '''
    
    if base.Base().dish(message.text):
        key1 = types.InlineKeyboardButton(text='Ингридиенты', callback_data='ingredient')
        key2 = types.InlineKeyboardButton(text='Себестоимость', callback_data='cost_price')
        key3 = types.InlineKeyboardButton(text='Маржинальность', callback_data='marge')
        key4 = types.InlineKeyboardButton(text='Удалить', callback_data='del')
        key5 = types.InlineKeyboardButton(text='Изменить', callback_data='edit')
        keyboard = types.InlineKeyboardMarkup().add(key1, key2, key3, key4, key5)
        await message.answer(text=message.text, reply_markup=keyboard)
    else:
        key1 = types.InlineKeyboardButton(text='Добавить', callback_data='add')
        keyboard = types.InlineKeyboardMarkup().add(key1)
        await message.answer(text=message.text, reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data)
async def call_info(call: types.CallbackQuery):
    if call.data == 'ingredient':  
        text = ''
        for num, d in enumerate(base.Base().ingredient_dish(call.message.text)):
            text += '{}.{}: {} (гр)\n'.format(num+1, d[0], d[1])
        await bot.send_message(call.from_user.id, text=text)
        await bot.answer_callback_query(call.id)
    if call.data == 'cost_price':  
        await bot.send_message(call.from_user.id, round(base.InfoDish(call.message.text).cost_price()))
        await bot.answer_callback_query(call.id)
    if call.data == 'marge':  
        await bot.send_message(call.from_user.id, round(base.InfoDish(call.message.text).marge(), 1))
        await bot.answer_callback_query(call.id)
    if call.data == 'add':  
        # запуск FSM для добавления ингридиентов
        await bot.answer_callback_query(call.id)
        dish.name = call.message.text
        await Form.ingredient.set()       
        await bot.send_message(call.from_user.id, "Введите ингридиент:")
    if call.data == 'del':  
        delete = base.DeleteDish(call.message.text)
        delete.delete()
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.from_user.id, "%s удален(о)" % call.message.text)
    if call.data == 'edit':  
        await bot.send_message(call.from_user.id, 'В разработке ...')
        await bot.answer_callback_query(call.id)


# States
class Form(StatesGroup):
    ingredient = State()  # Представление в хранилище как 'Form:ingredient'
    count = State()  # Представление в хранилище как 'Form:count'
    finish = State()
    price = State()


# Выход из FSM
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Отмена действия
    """
    await state.finish()
    # удаление клавиатуры
    await message.answer('Отменено!', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.ingredient)
async def process_name(message: types.Message, state: FSMContext):
    """
    Добавление ингридиента
    """
    ingredient = base.InfoIngredient(message.text)
    if ingredient.search_ingredient():
        async with state.proxy() as data:
            data['ingredient'] = message.text

        await Form.next()
        await message.answer("Какое количество (гр) %s?" %message.text)
    else:
        await message.answer('Ингредиента в базе нет')

# Проверка на число
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.count)
async def process_age_invalid(message: types.Message):
    """
    Валидация данных (int)
    """
    return await message.reply("Должно быть число!! Какое количество (гр)?")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.count)
async def process_age(message: types.Message, state: FSMContext):
    '''
    Добавление кол-ва ингридиента
    '''
    # Обновление шага и значения count
    await Form.next()
    await state.update_data(count=int(message.text))

    # Добавление Inline клавиатуры
    key1 = types.InlineKeyboardButton(text='Добавить', callback_data='next')
    key2 = types.InlineKeyboardButton(text='Закончить', callback_data='fin')
    keyboard = types.InlineKeyboardMarkup().add(key1, key2)

    await message.answer("Добавить еще ингридиент?", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data, state=Form.finish)
async def call_info(call: types.CallbackQuery, state: FSMContext):
    '''
    Перехват нажатия кнопки
    '''
    # Если продолжаем, возвращается к первому шагу
    if call.data == 'next':  
        await bot.answer_callback_query(call.id)
        await Form.first()
        await bot.send_message(call.from_user.id, text='Ингридиент:', reply_markup=types.ReplyKeyboardRemove())
        async with state.proxy() as data:
            data_ingr.append((data['ingredient'],data['count']))
    # Если заканчиваем, то выходим из FSM и выводим данные
    if call.data == 'fin':
        await bot.answer_callback_query(call.id)
        async with state.proxy() as data:
            data_ingr.append((data['ingredient'],data['count']))
            text = ''
            for num, d in enumerate(data_ingr):
                text += '{}.{}: {} (гр)\n'.format(num+1, d[0], d[1])
            await bot.send_message(
                call.from_user.id,
                text=text,
                reply_markup=types.ReplyKeyboardRemove()
            )
        await Form.next()
        await bot.send_message(call.from_user.id, 'Введите цену:')
        


@dp.callback_query_handler(lambda call: call.data, state=Form.price)
async def call_info(call: types.CallbackQuery, state: FSMContext):
    if call.data == 'Yes':
        await bot.answer_callback_query(call.id)
        dish.add_dish()
        for data in data_ingr:
            dish.add_ingredient(data[0], data[1])
        await state.finish()
    if call.data == 'No':
        await bot.answer_callback_query(call.id)
        await state.finish()

@dp.message_handler(lambda message: message.text, state=Form.price)
async def process_price(message: types.Message, state: FSMContext):
    dish.price = int(message.text)
    key1 = types.InlineKeyboardButton(text='Да', callback_data='Yes')
    key2 = types.InlineKeyboardButton(text='Нет', callback_data='No')
    keyboard = types.InlineKeyboardMarkup().add(key1, key2)
    await message.answer('Сохранить?', reply_markup=keyboard)


@dp.message_handler(lambda message: message.text, state=Form.finish)
async def process_gender_invalid(message: types.Message):
    """
    Валидация клавиш (Добавить, Закончить)
    """
    return await message.reply("Выбирите, пожалуйста")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)