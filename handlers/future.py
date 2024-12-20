# from sqlalchemy.future import select
#
#
# @dp.callback_query(F.data.startswith("members_"))
# async def list_clan_members(callback: types.CallbackQuery):
#     clan_id = int(callback.data.split("_")[1])  # Извлекаем ID клана
#
#     async with session_maker() as session:
#         try:
#             # Проверяем, существует ли клан
#             clan_result = await session.execute(
#                 select(Clan).where(Clan.clan_id == clan_id)
#             )
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Получаем участников клана
#             members_result = await session.execute(
#                 select(ClanMember.user_id).where(ClanMember.clan_id == clan_id)
#             )
#             members = members_result.scalars().all()
#
#             # Если в клане нет участников
#             if not members:
#                 await callback.message.edit_text(f"В клане '{clan.name}' пока нет участников.")
#                 return
#
#             # Формируем список участников
#             members_list = "\n".join([f"- {member}" for member in members])
#
#             # Отправляем пользователю список участников
#             await callback.message.edit_text(
#                 f"Список участников клана '{clan.name}':\n{members_list}"
#             )
#         except Exception as e:
#             # Обрабатываем ошибки
#             logging.exception(f"Error fetching members for clan {clan_id}: {e}")
#             await callback.message.edit_text("Произошла ошибка при получении списка участников.")
# Обработчик ввода telegram имени
# @dp.callback_query(F.data.startswith("join_clan"))
# async def join_clan(callback: types.CallbackQuery):
#     clan_id = int(callback.data.split("_")[1])  # Извлекаем ID клана
#     user_id = callback.from_user.id  # ID пользователя
#
#     async with session_maker() as session:  # Создаём сессию
#         try:
#             # Проверяем, состоит ли пользователь уже в каком-либо клане
#             existing_member = await session.execute(
#                 select(ClanMember).where(ClanMember.user_id == user_id)
#             )
#             if existing_member.scalars().first():
#                 await callback.message.edit_text("Вы уже состоите в клане.")
#                 return
#
#             # Проверяем, существует ли клан
#             clan_result = await session.execute(
#                 select(Clan).where(Clan.clan_id == clan_id)
#             )
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Добавляем пользователя в клан
#             new_member = ClanMember(clan_id=clan_id, user_id=user_id)
#             session.add(new_member)
#             await session.commit()
#
#             # Уведомляем пользователя о вступлении
#             await callback.message.edit_text(f"Вы успешно вступили в клан '{clan.name}'!")
#         except Exception as e:
#             # Обрабатываем ошибки
#             await callback.message.edit_text(f"Произошла ошибка: {str(e)}")
# @dp.callback_query(F.data.startswith("join_"))
# async def process_join_clan(callback: types.CallbackQuery, state: FSMContext):
#     try:
#         clan_id = int(callback.data.split("_")[1])
#         user_id = callback.from_user.id
#         user_name = callback.from_user.full_name
#
#         async with session_maker() as session:
#             # Проверяем, состоит ли пользователь уже в клане
#             result = await session.execute(select(ClanMember).where(ClanMember.user_id == user_id))
#             if result.scalars().first():
#                 await callback.message.edit_text("Вы уже состоите в клане.")
#                 return
#
#             # Получаем информацию о клане
#             clan_result = await session.execute(select(Clan).where(Clan.clan_id == clan_id))
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Уведомляем главу клана о запросе на вступление
#             leader_id = clan.leader_id
#             approve_buttons = InlineKeyboardMarkup(
#                 inline_keyboard=[
#                     [
#                         InlineKeyboardButton(text="Принять", callback_data=f"approve_{user_id}_{clan_id}"),
#                         InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}_{clan_id}")
#                     ]
#                 ]
#             )
#
#             await bot.send_message(
#                 chat_id=leader_id,
#                 text=f"Пользователь {user_name} хочет вступить в ваш клан '{clan.name}'. Что вы хотите сделать?",
#                 reply_markup=approve_buttons
#             )
#
#             await callback.message.edit_text(f"Запрос на вступление в клан '{clan.name}' отправлен главе клана. Ожидайте ответа.")
#     except ValueError:
#         await callback.message.edit_text("Некорректный идентификатор клана.")
#     except Exception as e:
#         await callback.message.edit_text(f"Произошла ошибка: {str(e)}")
# @dp.callback_query(F.data.startswith("join_clan"))
# async def join_clan(callback: types.CallbackQuery):
#     clan_id = int(callback.data.split("_")[1])  # Извлекаем ID клана
#     user_id = callback.from_user.id  # ID пользователя
#
#     async with session_maker() as session:  # Создаём сессию
#         try:
#             # Проверяем, состоит ли пользователь уже в каком-либо клане
#             existing_member = await session.execute(
#                 select(ClanMember).where(ClanMember.user_id == user_id)
#             )
#             if existing_member.scalars().first():
#                 await callback.message.edit_text("Вы уже состоите в клане.")
#                 return
#
#             # Проверяем, существует ли клан
#             clan_result = await session.execute(
#                 select(Clan).where(Clan.clan_id == clan_id)
#             )
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Добавляем пользователя в клан
#             new_member = ClanMember(clan_id=clan_id, user_id=user_id)
#             session.add(new_member)
#             await session.commit()
#
#             # Уведомляем пользователя о вступлении
#             await callback.message.edit_text(f"Вы успешно вступили в клан '{clan.name}'!")
#         except Exception as e:
#             # Обрабатываем ошибки
#             await callback.message.edit_text(f"Произошла ошибка: {str(e)}")
# @dp.callback_query(F.data.startswith("join_"))
# async def process_join_clan(callback: types.CallbackQuery, state: FSMContext):
#     try:
#         clan_id = int(callback.data.split("_")[1])
#         user_id = callback.from_user.id
#         user_name = callback.from_user.full_name
#
#         async with session_maker() as session:
#             # Проверяем, состоит ли пользователь уже в клане
#             result = await session.execute(select(ClanMember).where(ClanMember.user_id == user_id))
#             if result.scalars().first():
#                 await callback.message.edit_text("Вы уже состоите в клане.")
#                 return
#
#             # Получаем информацию о клане
#             clan_result = await session.execute(select(Clan).where(Clan.clan_id == clan_id))
#             clan = clan_result.scalars().first()
#             if not clan:
#                 await callback.message.edit_text("Клан не найден.")
#                 return
#
#             # Уведомляем главу клана о запросе на вступление
#             leader_id = clan.leader_id
#             approve_buttons = InlineKeyboardMarkup(
#                 inline_keyboard=[
#                     [
#                         InlineKeyboardButton(text="Принять", callback_data=f"approve_{user_id}_{clan_id}"),
#                         InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{user_id}_{clan_id}")
#                     ]
#                 ]
#             )
#
#             await bot.send_message(
#                 chat_id=leader_id,
#                 text=f"Пользователь {user_name} хочет вступить в ваш клан '{clan.name}'. Что вы хотите сделать?",
#                 reply_markup=approve_buttons
#             )
#
#             await callback.message.edit_text(f"Запрос на вступление в клан '{clan.name}' отправлен главе клана. Ожидайте ответа.")
#     except ValueError:
#         await callback.message.edit_text("Некорректный идентификатор клана.")
#     except Exception as e:
#         await callback.message.edit_text(f"Произошла ошибка: {str(e)}")
