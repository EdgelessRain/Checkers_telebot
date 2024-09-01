import telebot
from telebot import types # для указание типов
from keyboa import Keyboa
import sqlite3
from contextlib import closing
import sys
import pathlib
from copy import deepcopy
import operator
operatorlookup = {
    '+': operator.add,
    '-': operator.sub
}

first_player = 0 #Никнейм первого игрока
id_fplayer = 0
second_player = 0 #Никнейм второго игрока
id_splayer = 0
invite_player = 0
step = int(0) #Счёт ходов
stage = int(0) #Стадия хода, 0 - выбор шашки, 1 - выбор куда ей идти
position = [0, 0] #Массив начальной и конечной позиции шашки
bot = telebot.TeleBot('Ваш токен бота');  #Связывание бота с данной программой через токен
possibility_of_the_continuations = bool(0)

database = 'users_statistic.db'

# Функция для инициализации базы данных
def init_db():

    script_path = pathlib.Path(sys.argv[0]).parent
    db_path = script_path / 'users_statistic.db'

    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # Создаем таблицу, если она отсутствует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            rating INTEGER,
            quantity INTEGER,
            win INTEGER,
            lose INTEGER,
            draw INTEGER
        )
    ''')

    conn.commit()
    return conn, cursor


# Связывание бота с базой данных игроков
conn, cursor = init_db()

#Занесение данных нового игрока
def db_table_val(user_id: int, rating: int, quantity: int, win: int, lose: int, draw: int):
    cursor.execute('INSERT INTO users (user_id, rating, quantity, win, lose, draw) VALUES (?, ?, ?, ?, ?, ?)', (user_id, rating, quantity, win, lose, draw))
    conn.commit()

#Проверяем, есть ли юзер в базе
def user_exists(user_id):
    result = cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
    return bool(len(result.fetchall()))

#Обновление таблицы по результатам игры
def update_table(user_id, itog):
    with closing(sqlite3.connect(database)) as connection:
        connection.row_factory = sqlite3.Row
        cursor.execute("SELECT  * FROM `users` ")
        for i in cursor.fetchall():
            # получаем значения по строке
            if user_id == i[1]:
                rating = i[2]
                quantity = i[3]
                win = i[4]
                lose = i[5]
                draw = i[6]
 
    if itog == 0:
        rating -= 30
        quantity += 1
        lose += 1
    elif itog == 1:
        quantity += 1
        draw += 1
    elif itog == 2:
        rating += 30
        quantity += 1
        win += 1
    cursor.execute("UPDATE users SET rating =  ?, quantity = ?, win = ?, lose = ?, draw = ? WHERE user_id = ?", (rating, quantity, win, lose, draw, user_id,))
    conn.commit()

#Обнуление глобальных переменных
def end_game():
    global field
    global defoult_field
    global step
    global stage
    global first_player 
    global second_player
    global id_fplayer
    global id_splayer
    global position
    global invite_player
    global possibility_of_the_continuations
    field = deepcopy(defoult_field)
    step = 0
    stage = 0
    first_player = 0
    second_player = 0
    id_fplayer = 0
    id_splayer = 0
    position = [0, 0]
    invite_player = 0
    possibility_of_the_continuations = 0

#массив словарей, которые содержпт в себе ячейку со своей "координатой"
defoult_field = [
        {' ': 11}, {'⚫': 12}, {' ': 13}, {'⚫': 14}, {' ': 15}, {'⚫': 16}, {' ': 17}, {'⚫': 18},
        {'⚫': 21}, {' ': 22}, {'⚫': 23}, {' ': 24}, {'⚫': 25}, {' ': 26}, {'⚫': 27}, {' ': 28},
        {' ': 31}, {'⚫': 32}, {' ': 33}, {'⚫': 34}, {' ': 35}, {'⚫': 36}, {' ': 37}, {'⚫': 38},
        {' ': 41}, {' ': 42}, {' ': 43}, {' ': 44}, {' ': 45}, {' ': 46}, {' ': 47}, {' ': 48},
        {' ': 51}, {' ': 52}, {' ': 53}, {' ': 54}, {' ': 55}, {' ': 56}, {' ': 57}, {' ': 58},
        {'⚪': 61}, {' ': 62}, {'⚪': 63}, {' ': 64}, {'⚪': 65}, {' ': 66}, {'⚪': 67}, {' ': 68},
        {' ': 71}, {'⚪': 72}, {' ': 73}, {'⚪': 74}, {' ': 75}, {'⚪': 76}, {' ': 77}, {'⚪': 78},
        {'⚪': 81}, {' ': 82}, {'⚪': 83}, {' ': 84}, {'⚪': 85}, {' ': 86}, {'⚪': 87}, {' ': 88},
        {'Сдаться': 'capitulate'}, {'Предложить ничью': 'draw'}]

field = deepcopy(defoult_field)

#Обработка команды /start
@bot.message_handler(commands = ['start'])
def launch(message):
    bot.send_message(message.chat.id, 'Привет! Чтобы начать игру введите /play. Чтобы узнать правила введите /rules')
   
#Обработка команды /play
@bot.message_handler(commands = ['play'])
def launch(message):
    global first_player
    global id_fplayer
    markup = types.InlineKeyboardMarkup();
    btn1 = types.InlineKeyboardButton(text = '🌚 Начать игру', callback_data= 'start')
    markup.add(btn1)
    btn2 = types.InlineKeyboardButton(text = 'Отмена', callback_data = 'close')
    markup.add(btn2)
    first_player = message.from_user.first_name
    id_fplayer = message.from_user.id
    #проверка, есть ли первй игрок в базе данных
    if user_exists(message.from_user.id) == 0:
        db_table_val(message.from_user.id, 1000, 0, 0, 0, 0)
        bot.send_message(message.chat.id, 'Привет! Вы добавлены в базу данных!')
    else:
        bot.send_message(message.chat.id, text="Привет, {0.first_name}!".format(message.from_user), reply_markup=markup)

#Обработка команды /rules
@bot.message_handler(commands = ['rules'])
def rules(message):
    bot.send_message(message.chat.id, """
Это английские шашки.
Шашки ходят только вперёд. 
Простая шашка бьёт только вперёд , "перепрыгивая" через шашку соперника на следующее поле.
Если есть возможность бить, то бить обязательно.
Дамка ходит вперёд и назад на одну клетку по диагонали. Дамка бьёт вперёд и назад.
Во время игры простая шашка может превратиться в дамку.""")

#Обработка команды /agree
@bot.message_handler(commands = ['agree']) 
def agree(message):
    global first_player
    global second_player
    global id_fplayer
    global id_splayer
    global invite_player
    print(invite_player)
    print(id_fplayer)
    print(id_splayer)
    print(message.from_user.id)
    print(message.text)
    if invite_player == id_fplayer and message.from_user.id == id_splayer:
        bot.send_message(message.chat.id, 'Ничья! Игроки ничего не получили')  
        update_table(id_splayer, 1) 
        update_table(id_fplayer, 1)   
        end_game()   
        return       
    if invite_player == id_splayer and message.from_user.id == id_fplayer:
        bot.send_message(message.chat.id, 'Ничья! Игроки ничего не получили')  
        update_table(id_splayer, 1) 
        update_table(id_fplayer, 1)  
        end_game()
        return     

#Обработка при нажатии кнопки '🌚 Начать игру'
@bot.callback_query_handler(func=lambda call: call.data == 'start')
def add_second_player(call):
    global first_player
    markup = types.InlineKeyboardMarkup();
    btn1 = types.InlineKeyboardButton(text = 'Присоединиться к партии', callback_data= 'join')
    markup.add(btn1)
    bot.send_message(call.message.chat.id, "Игрок ждёт соперника", reply_markup=markup)

#Обработка при нажатии кнопки 'Отмена'
@bot.callback_query_handler(func=lambda call: call.data == 'close')  
def close(call):

     bot.send_message( call.message.chat.id, "До встречи, " + str(call.from_user.first_name))
     end_game()
     return 

#Обработка при нажатии кнопки 'Присоединиться к партии'
@bot.callback_query_handler(func=lambda call: call.data == 'join')        
def start_game(call):
    global field
    global second_player
    global id_splayer
    """заменить на call.from_user.id == id_fplayer если надо потестить одному"""
    if call.from_user.id != id_fplayer:
        #проверка, есть ли второй игрок в базе данных
        if user_exists(call.from_user.id) == 0:
            db_table_val(call.from_user.id, 1000, 0, 0, 0, 0)
        second_player = call.from_user.first_name
        id_splayer = call.from_user.id
        game = Keyboa(items=field, copy_text_to_callback=True, items_in_row=8)

        bot.send_message(call.message.chat.id, 'ходит игрок ' +str(first_player) +'!', reply_markup=game())
    

#Обработка при нажатии кнопки 'Сдаться'
@bot.callback_query_handler(func=lambda call: call.data == 'capitulate')        
def capitulate(call):
    global first_player
    global second_player
    global id_fplayer
    global id_splayer

    if (call.from_user.first_name == second_player):
        bot.send_message(call.message.chat.id, 'выиграл  ' +str(first_player) +'!!!. Он получает +30 рейтинга.')  
        update_table(id_fplayer, 2) 
        update_table(id_splayer, 0)
        end_game()
        return 

    elif (call.from_user.first_name == first_player):
        bot.send_message(call.message.chat.id, 'выиграл  ' +str(second_player) +'!!!. Он получает +30 рейтинга.')  
        update_table(id_splayer, 2) 
        update_table(id_fplayer, 0)
        end_game()
        return 

#Обработка при нажатии кнопки 'Предложить ничью'
@bot.callback_query_handler(func=lambda call: call.data == 'draw')        
def draw(call):
    global invite_player
    if call.from_user.id == id_fplayer or call.from_user.id == id_splayer: 
        invite_player = call.from_user.id
        bot.send_message(call.message.chat.id, 'Игрок ' +str(call.from_user.first_name) +' предлагает ничью. Напишите /agree если согласны.') 


              

#Обработка ходов
@bot.callback_query_handler(func=lambda call: True)
def steps(call):
    global step
    global first_player
    global second_player
    global stage 
    global field
    global position
    global id_fplayer
    global id_splayer
    validate = 1
    global possibility_of_the_continuations

    if  (step % int(2) == 0):
        antikey = '⚫'
        antidamkey = '⬛'
        key = '⚪'
        damkey = '⬜'
        player = first_player
        player_2 = second_player
        id_player1 = id_fplayer
        id_player2 = id_splayer
    else:
        antikey = '⚪'
        antidamkey = '⬜'
        key = '⚫'
        damkey = '⬛'
        player = second_player
        player_2 = first_player
        id_player1 = id_splayer
        id_player2 = id_fplayer 
    
    places_of_player = []
    for index, dict_ in enumerate(field):
        if key in dict_ or damkey in dict_:
            places_of_player += list(dict_.values())

    places_of_player2_end = 0  
    places_of_player2 = 0
    for index, dict_ in enumerate(field):
        if antikey in dict_ or antidamkey in dict_:
            places_of_player2 += 1

    if len(list(dict_.values())) == 0:
        bot.send_message(call.message.chat.id, 'выиграл  ' +str(player_2) +'!!!. Он по-лучает +30 рейтинга.')
        update_table(id_player2, 2) 
        update_table(id_player1, 0)
        end_game()
        return 
    if places_of_player2 == 0:
        bot.send_message(call.message.chat.id, 'выиграл  ' +str(player) +'!!!. Он полу-чает +30 рейтинга.')
        update_table(id_player1, 2) 
        update_table(id_player2, 0)
        end_game()
        return 

    if (call.from_user.first_name == player):
        if stage == 0:
            position[stage] = int(call.data)
            if position[stage] in places_of_player:
                stage = 1
        elif stage == 1 and possibility_of_the_continuations == 0:
            position[stage]  = int(call.data) 
            if position[stage] in places_of_player:
                position[stage-1] = position[stage]
                position[stage] = 0
            
            elif bool(check_motion()) == 1 and position[1] != 0:
                if bool(opportunity_to_eat(validate)) != 1:
                    game = Keyboa(items=field, copy_text_to_callback=True, items_in_row=8)
                    bot.send_message(call.message.chat.id, 'ходит игрок ' +str(player_2) +'!', reply_markup=game())
                    position = [0, 0]
                    stage = 0
                    possibility_of_the_continuations = 0 
                    step += 1
                      
                else:
                    for index, dict_ in enumerate(field):
                        if antikey in dict_ or antidamkey in dict_:
                            places_of_player2_end += 1
                    if places_of_player2_end < places_of_player2:
                        game = Keyboa(items=field, copy_text_to_callback=True, items_in_row=8)
                        bot.send_message(call.message.chat.id, 'продолжает '+ str(player) +'!', reply_markup=game())   
                        possibility_of_the_continuations = 1 
                    else:
                        game = Keyboa(items=field, copy_text_to_callback=True, items_in_row=8)
                        bot.send_message(call.message.chat.id, 'ходит игрок ' +str(player_2) +'!', reply_markup=game())
                        position = [0, 0]
                        stage = 0
                        possibility_of_the_continuations = 0 
                        step += 1    
                
        elif stage == 1 and possibility_of_the_continuations == 1:
            position[stage-1] = position[stage]
            position[stage]  = int(call.data) 
            if bool(check_motion()) == 1 and position[1] != 0:
                if bool(opportunity_to_eat(validate)) != 1:
                    game = Keyboa(items=field, copy_text_to_callback=True, items_in_row=8)
                    bot.send_message(call.message.chat.id, 'ходит игрок ' +str(player_2) +'!', reply_markup=game())
                    position = [0, 0]
                    stage = 0
                    possibility_of_the_continuations = 0 
                    step += 1
                    
                else:
                    for index, dict_ in enumerate(field):
                        if antikey in dict_ or antidamkey in dict_:
                            places_of_player2_end += 1
                    if places_of_player2_end < places_of_player2:
                        game = Keyboa(items=field, copy_text_to_callback=True, items_in_row=8)
                        bot.send_message(call.message.chat.id, 'продолжает '+ str(player) +'!', reply_markup=game())   
                        possibility_of_the_continuations = 1 
                    else:
                        game = Keyboa(items=field, copy_text_to_callback=True, items_in_row=8)
                        bot.send_message(call.message.chat.id, 'ходит игрок ' +str(player_2) +'!', reply_markup=game())
                        position = [0, 0]
                        stage = 0
                        possibility_of_the_continuations = 0 
                        step += 1           

            

#Проверка, удовлетворяет ли ход правилам
def check_motion():
    global position
    global field
    global step
    validate= 0
    x = 0 
    
    if  (step % int(2) == 1):
        antikey = '⚪'
        antidamkey = '⬜'
        key = '⚫'
        damkey = '⬛'
        sign = '-'
        antisign = '+'
        last_row = [81, 82, 83, 84, 85, 86, 87, 88]
    else:
        antikey = '⚫'
        antidamkey = '⬛'
        key = '⚪'
        damkey = '⬜'
        sign = '+'    
        antisign = '-'
        last_row = [11, 12, 13, 14, 15, 16, 17, 18]

    op = operatorlookup.get(sign)
    antiop = operatorlookup.get(antisign)
    for index, dict_ in enumerate(field):
        if list(dict_.values())[0] == position[0]:
            if dict_.get(key):
                
                #проверка условий, что игрок съел фигуру
                if position[0] == op(position[1], 22) or  position[0] == op(position[1], 18): #or position[0] == antiop(position[1], 22) or position[0] == antiop(position[1], 18):
                    for index, dict_ in enumerate(field):
                        if list(dict_.values())[0] == position[1]:
                            if ' ' in dict_: continue
                            else: return False
                    for index1, dict1 in enumerate(field):
                        if list(dict1.values())[0] == position[0]:
                            dict1[' '] = dict1.pop(key) 
                            for index2, dict2 in enumerate(field):
                                if list(dict2.values())[0] == position[1]:
                                    dict2[key] = dict2.pop(' ')

                                    for index3, dict3 in enumerate(field):
                                        if list(dict3.values())[0] == int(((position[0] + position[1])/2)) and ((antikey in dict3) or (antidamkey in dict3)):
                                            if antikey in dict3:
                                                dict3[' '] = dict3.pop(antikey)
                                            elif antidamkey in dict3:
                                                dict3[' '] = dict3.pop(antidamkey)
                                            x = 1
                                            break
                                    if x == 0: return False

                #проверка условий, что игрок просто сходил     
                                
                elif (position[0] == op(position[1], 9) or  position[0] == op(position[1], 11)):
                    if  bool(opportunity_to_eat(validate)) == 1 : return False
                    for index, dict_ in enumerate(field):
                        if list(dict_.values())[0] == position[1]:
                            if ' ' in dict_: continue
                            else: return False
                    for index1, dict1 in enumerate(field):
                
                        if list(dict1.values())[0] == position[0]:
                            dict1[' '] = dict1.pop(key)
                            for index2, dict1 in enumerate(field):
                                if list(dict1.values())[0] == position[1]:
                                    dict1[key] = dict1.pop(' ')       
                else: return False

                #Достижение конца поля и становление дамкой
                if position[1] in last_row:
                    for index, dict_ in enumerate(field):
                                if list(dict_.values())[0] == position[1]:
                                    dict_[damkey] = dict_.pop(key)
                return True

            elif dict_.get(damkey):
                #проверка условий, что игрок съел фигуру
                if position[0] == op(position[1], 22) or  position[0] == op(position[1], 18) or position[0] == antiop(position[1], 22) or position[0] == antiop(position[1], 18):
                    for index, dict_ in enumerate(field):
                        if list(dict_.values())[0] == position[1]:
                            if ' ' in dict_: continue
                            else: return False
                    for index1, dict1 in enumerate(field):
                        if list(dict1.values())[0] == position[0]:
                            dict1[' '] = dict1.pop(damkey)    
                            for index2, dict2 in enumerate(field):
                                if list(dict2.values())[0] == position[1]:
                                    dict2[damkey] = dict2.pop(' ')

                                    for index3, dict3 in enumerate(field):
                                        if list(dict3.values())[0] == int(((position[0] + position[1])/2)) and ((antikey in dict3) or (antidamkey in dict3)):
                                            if antikey in dict3:
                                                dict3[' '] = dict3.pop(antikey)
                                            elif antidamkey in dict3:
                                                dict3[' '] = dict3.pop(antidamkey)
                                            x = 1
                                            break
                                    if x == 0: return False

                #проверка условий, что игрок просто сходил                      
                elif (position[0] == op(position[1], 9) or  position[0] == op(position[1], 11) or position[0] == antiop(position[1], 9) or position[0] == antiop(position[1], 11)):
                    if  bool(opportunity_to_eat(validate)) == 1 : return False
                    for index, dict_ in enumerate(field):
                        if list(dict_.values())[0] == position[1]:
                            if ' ' in dict_: continue
                            else: return False
                    for index1, dict1 in enumerate(field):
                
                        if list(dict1.values())[0] == position[0]:
                            dict1[' '] = dict1.pop(damkey)
                            for index2, dict1 in enumerate(field):
                                if list(dict1.values())[0] == position[1]:
                                    dict1[damkey] = dict1.pop(' ')       
                else: return False
                return True


#Проверка, есть ли возможность съесть
def opportunity_to_eat(validate):
    global position
    global field
    global step

    if  (step % int(2) == 1):
        antikey = '⚪'
        antidamkey = '⬜'
        key = '⚫'
        damkey = '⬛'
        sign = '-'
        antisign = '+'
    else:
        antikey = '⚫'
        antidamkey = '⬛'
        key = '⚪'
        damkey = '⬜'
        sign = '+'
        antisign = '-'

    op = operatorlookup.get(sign)
    antiop = operatorlookup.get(antisign)

    if validate == 0:
        for index, dict_ in enumerate(field):
            if key  in dict_:
                for index1, dict1 in enumerate(field):
                    if  (list(dict1.values())[0] == antiop(list(dict_.values())[0], 9) and ((antikey in dict1) or (antidamkey in dict1)) or 
                    (list(dict1.values())[0] == antiop(list(dict_.values())[0], 11) and ((antikey in dict1) or (antidamkey in dict1)))):
                        for index2, dict2 in enumerate(field):
                            if ((list(dict2.values())[0] == antiop(list(dict1.values())[0], 11) and list(dict1.values())[0] == antiop(list(dict_.values())[0], 11) and (' ' in dict2)) or
                            (list(dict2.values())[0] == antiop(list(dict1.values())[0], 9) and list(dict1.values())[0] == antiop(list(dict_.values())[0], 9) and (' ' in dict2)))and ((antikey in dict1) or (antidamkey in dict1)):
                                return True
            elif damkey in dict_:     
                for index1, dict1 in enumerate(field):
                    if (list(dict1.values())[0] == list(dict_.values())[0] + 11 or
                    list(dict1.values())[0] == list(dict_.values())[0] - 11 or
                    list(dict1.values())[0] == list(dict_.values())[0] + 9 or
                    list(dict1.values())[0] == list(dict_.values())[0] - 9) and ((antikey in dict1) or (antidamkey in dict1)):

                        for index2, dict2 in enumerate(field):
                            if (list(dict2.values())[0] == list(dict1.values())[0] + 11 and (' ' in dict2) and (list(dict1.values())[0] == list(dict_.values())[0] + 11 or
                            (list(dict2.values())[0] == list(dict1.values())[0] - 11 and (' ' in dict2) and list(dict1.values())[0] == list(dict_.values())[0] - 11) or
                            (list(dict2.values())[0] == list(dict1.values())[0] + 9 and (' ' in dict2) and  list(dict1.values())[0] == list(dict_.values())[0] + 9) or
                            (list(dict2.values())[0] == list(dict1.values())[0] - 9 and (' ' in dict2) and list(dict1.values())[0] == list(dict_.values())[0] - 9))) and ((antikey in dict1) or (antidamkey in dict1)):
            
                                return True
        return False            
       
    elif validate == 1:
        x = 1
        for index1, dict1 in enumerate(field):
            for index, dict_ in enumerate(field):
                if dict_.get(key) == position[1]:
                    x = 1
                    break
                elif dict_.get(damkey) == position[1]:
                    x = 2
                    break
            if x == 2:
                if (list(dict1.values())[0] ==position[1] + 11 or
                list(dict1.values())[0] ==position[1] - 11 or
                list(dict1.values())[0] ==position[1] + 9 or
                list(dict1.values())[0] ==position[1] - 9) and ((antikey in dict1) or (antidamkey in dict1)):
                    for index2, dict2 in enumerate(field):
                        if ((list(dict2.values())[0] ==position[1] + 22 and list(dict2.values())[0] == list(dict1.values())[0] + 11 and ' ' in dict2) or
                        (list(dict2.values())[0] ==position[1] - 22  and list(dict2.values())[0] == list(dict1.values())[0] - 11 and ' ' in dict2) or
                        (list(dict2.values())[0] ==position[1] + 18 and list(dict2.values())[0] == list(dict1.values())[0] + 9 and ' ' in dict2) or
                        (list(dict2.values())[0] ==position[1] - 18 and list(dict2.values())[0] == list(dict1.values())[0] - 9 and ' ' in dict2)):
                            return True
            elif x == 1:
                if (list(dict1.values())[0] == antiop(position[1], 9) and ((antikey in dict1) or (antidamkey in dict1)) or 
                (list(dict1.values())[0] == antiop(position[1], 11) and ((antikey in dict1) or (antidamkey in dict1)))):
                    for index2, dict2 in enumerate(field):
                        if ((list(dict2.values())[0] ==  antiop(position[1], 22) and list(dict2.values())[0] == antiop(list(dict1.values())[0], 11) and ' ' in dict2) or
                        (list(dict2.values())[0] == antiop(position[1], 18) and list(dict2.values())[0] == antiop(list(dict1.values())[0], 9) and ' ' in dict2)):
                            return True
        

        return False

bot.polling(none_stop=True, interval=0)
