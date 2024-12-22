# ChessBot — Телеграмм-бот для игры в шахматы
Целью данной курсовой работы является разработка телеграмм-бота для игры в шахматы.  

## Команда проекта:
- Давар Рафаил 4215
- Храмова Ева 4215
- Герасимов Николай 4215

## ▎Правила игры в шахматы:

Цель игры — поставить короля противника под шах и мат, что означает, что он не может сделать ни одного законного хода, чтобы избежать захвата.

Размер игрового поля — 8x8 клеток (всего 64 клетки).

Правила перемещения фигур:

• Пешка: движется вперед на одну клетку, но бьет по диагонали. При первом ходе может двигаться на две клетки.

• Ладья: движется по вертикали или горизонтали на любое количество клеток.

• Конь: движется буквой "Г" (две клетки в одном направлении и одна клетка в перпендикулярном).

• Слон: движется по диагонали на любое количество клеток.

• Ферзь: комбинирует ходы слона и ладьи, может двигаться в любом направлении на любое количество клеток.

• Король: может двигаться на одну клетку в любом направлении.

Возможные исходы игры:

• Игрок побеждает, ставя короля противника под шах и мат.

• Игрок побеждает, если противник сдается.

• Игра может закончиться вничью по соглашению игроков или в случае патовой ситуации (король не под шахом, но нет доступных ходов).

• Игрок досрочно проигрывает при нажатии на кнопку "сдаться".


## Стек технологий:
1.  Язык программирования:
    * **Python** — основной язык для разработки бота. Python используется благодаря своей простоте и широким возможностям для работы с различными библиотеками и фреймворками.
      
2.  Библиотека для работы с Telegram API:
    * **aiogram** — это мощный и гибкий фреймворк для создания телеграмм‑ботов на Python. С его помощью мы можем быстро и легко реализовать сложные сценарии взаимодействия, предоставляя пользователям интуитивно понятный интерфейс.
      
3.  Работа с БД:
    * **SQLAlchemy** — библиотека для работы с базой данных, которая позволяет взаимодействовать с реляционными базами данных через объектно-ориентированную модель. Используется для удобной работы с данными и их хранением.
   
## To-do list
• [+] Реализация графического интерфейса для отображения шахматной доски

• [ ] Разработка логики игры (правила, проверки на шах и мат)

• [+] Разработка движения фигур

• [ ] Поддержка одновременного подключения множества игроков (2 человека) для совместной игры

• [+] Реализация базы данных на SQLAlchemy

• [ ] Добавление оплаты

• [+] Добвление магазина

• [ ] Добавление Кланов

• [ ] Добавление скинов

- [ ] ...