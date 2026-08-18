import asyncio
import io
import pandas as pd
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile
)

from config import BOT_TOKEN, ADMIN_ID, SHTAB_GROUP_ID
import database as db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class RegState(StatesGroup):
    full_name = State()
    role = State()

class VoteState(StatesGroup):
    phone = State()
    captcha = State()
    sms = State()

def main_kb(is_admin=False):
    kb = [
        [KeyboardButton(text="➕ Yangi ovoz kiritish")],
        [KeyboardButton(text="📊 Mening natijalarim"), KeyboardButton(text="🏆 TOP-30 Reyting")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="📑 Pullik agentlar hisoboti (Excel)")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if user:
        await message.answer(
            f"Hush kelibsiz, **{user['full_name']}**!\nMaqomingiz: **{user['role']}**",
            reply_markup=main_kb(message.from_user.id == ADMIN_ID),
            parse_mode="Markdown"
        )
    else:
        await message.answer("Assalomu alaykum! Iltimos, ism va familiyangizni kiriting:")
        await state.set_state(RegState.full_name)

@dp.message(RegState.full_name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    
    role_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Pullik agent", callback_data="role_Pullik agent")],
        [InlineKeyboardButton(text="🤝 Volontyor (Ko'ngilli)", callback_data="role_Volontyor")]
    ])
    await message.answer("Faoliyat turini tanlang:", reply_markup=role_kb)
    await state.set_state(RegState.role)

@dp.callback_query(RegState.role, F.data.startswith("role_"))
async def reg_role(callback: types.CallbackQuery, state: StateContext):
    role = callback.data.split("_")[1]
    data = await state.get_data()
    
    await db.add_user(callback.from_user.id, data['full_name'], role)
    await state.clear()
    
    await callback.message.delete()
    await callback.message.answer(
        f"Muvaffaqiyatli ro'yxatdan o'tdingiz!\n👤 Ism: {data['full_name']}\n📌 Turi: {role}",
        reply_markup=main_kb(callback.from_user.id == ADMIN_ID)
    )

@dp.message(F.text == "➕ Yangi ovoz kiritish")
async def start_vote(message: types.Message, state: FSMContext):
    await message.answer("Mijoz telefon raqamini kiriting:\n*(Masalan: 998901234567)*")
    await state.set_state(VoteState.phone)

@dp.message(VoteState.phone)
async def vote_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip().replace("+", "")
    if not phone.isdigit() or len(phone) < 9:
        await message.answer("❌ Noto'g'ri raqam formati. Qaytadan kiriting:")
        return
    
    await state.update_data(phone=phone)
    # Bu yerda Open Budget'dan olingan Kapcha taqdim etiladi
    await message.answer("Open Budget'dan olingan Kapcha kodini kiriting:\n*(Simulyatsiya: 4 xonali son)*")
    await state.set_state(VoteState.captcha)

@dp.message(VoteState.captcha)
async def vote_captcha(message: types.Message, state: FSMContext):
    await message.answer("📱 Mijozga borgan SMS kodni kiriting:")
    await state.set_state(VoteState.sms)

@dp.message(VoteState.sms)
async def vote_sms(message: types.Message, state: FSMContext):
    data = await state.get_data()
    phone = data['phone']
    user = await db.get_user(message.from_user.id)
    
    # 3 xil ehtimoliy natija simulyatsiyasi (Amalda Open Budget API statusini qaytaradi)
    # Natija: 'Qabul qilindi', 'Rad etildi' yoki 'Jarayonda'
    status = "Jarayonda"  # Test uchun
    
    vote_id = await db.add_vote(message.from_user.id, phone, status)
    await state.clear()

    if status == "Qabul qilindi":
        await message.answer(
            f"🟢 **OVOZ QABUL QILINDI!**\n📱 Raqam: `+{phone}`\nHisob-kitob qilishingiz mumkin.",
            reply_markup=main_kb(message.from_user.id == ADMIN_ID),
            parse_mode="Markdown"
        )
    elif status == "Rad etildi":
        await message.answer(
            f"🔴 **OVOZ RAD ETILDI!**\n📱 Raqam: `+{phone}`\nOvoz ilgari berilgan. Pul to'lamang!",
            reply_markup=main_kb(message.from_user.id == ADMIN_ID),
            parse_mode="Markdown"
        )
    else:  # Jarayonda
        if user['role'] == "Pullik agent":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Shtabga tekshirish uchun yuborish", callback_data=f"shtab_{vote_id}")],
                [InlineKeyboardButton(text="➕ Keyingi mijozga o'tish", callback_data="next_client")]
            ])
            text = (
                f"⏳ **OVOZ HOZIR 'JARAYONDA' STATUSIDA!**\n\n"
                f"📱 Raqam: `+{phone}`\n\n"
                f"🚨 **DIQQAT! RAQAM EGASIGA PUL TO'LAMANG!**\n"
                f"Tizim JSHSHIR bo'yicha tekshirmoqda. Baza tasdiqlamaguncha kutib turing.\n\n"
                f"Shtabga tekshirish uchun yuborasizmi?"
            )
            await message.answer(text, reply_markup=kb, parse_mode="Markdown")
        else:
            await message.answer(
                f"⏳ **OVOZ JARAYONDA (TEKSHIRUVDA)!**\n📱 Raqam: `+{phone}`\nTekshiruv yakunlangach hisobga o'tadi.",
                reply_markup=main_kb(message.from_user.id == ADMIN_ID),
                parse_mode="Markdown"
            )

@dp.callback_query(F.data.startswith("shtab_"))
async def to_shtab(callback: types.CallbackQuery):
    vote_id = int(callback.data.split("_")[1])
    user = await db.get_user(callback.from_user.id)
    
    shtab_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Qabul qilindi", callback_data=f"res_Qabul qilindi_{vote_id}_{callback.from_user.id}"),
            InlineKeyboardButton(text="🔴 Rad etildi", callback_data=f"res_Rad etildi_{vote_id}_{callback.from_user.id}")
        ]
    ])
    
    async with db.pool.acquire() as conn:
        v = await conn.fetchrow("SELECT phone FROM votes WHERE id = $1", vote_id)
        phone = v['phone']
        
    await bot.send_message(
        chat_id=SHTAB_GROUP_ID,
        text=f"🔍 **TEKSHIRUV SO'ROVI**\n👤 Agent: {user['full_name']} (Pullik)\n📱 Raqam: `+{phone}`",
        reply_markup=shtab_kb,
        parse_mode="Markdown"
    )
    await callback.answer("Shtabga yuborildi! Keyingi mijoz bilan ishlayvering.", show_alert=True)

@dp.callback_query(F.data.startswith("res_"))
async def shtab_res(callback: types.CallbackQuery):
    _, status, vote_id, agent_id = callback.data.split("_")
    vote = await db.update_vote_status(int(vote_id), status)
    
    await callback.message.edit_text(
        callback.message.text + f"\n\n Yakuniy xulosa: **{status}**",
        parse_mode="Markdown"
    )
    
    msg = (
        f"📢 **Shtab tekshiruvi yakunlandi!**\n📱 `+{vote['phone']}`\nNatija: **{status}**"
    )
    try:
        await bot.send_message(chat_id=int(agent_id), text=msg, parse_mode="Markdown")
    except:
        pass

@dp.callback_query(F.data == "next_client")
async def next_c(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Keyingi mijoz telefon raqamini kiriting:\n*(Masalan: 998901234567)*")
    await state.set_state(VoteState.phone)

@dp.message(F.text == "📊 Mening natijalarim")
async def stats_view(message: types.Message):
    stats = await db.get_agent_stats(message.from_user.id)
    await message.answer(
        f"📊 **SIZNING NATIJALARINGIZ:**\n\n"
        f"🟢 Qabul qilingan: {stats.get('Qabul qilindi', 0)} ta\n"
        f"⏳ Jarayonda: {stats.get('Jarayonda', 0)} ta\n"
        f"🔴 Rad etilgan: {stats.get('Rad etildi', 0)} ta",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🏆 TOP-30 Reyting")
async def top_view(message: types.Message):
    top_list = await db.get_top_30()
    if not top_list:
        await message.answer("Reyting hali shakllanmadi.")
        return
        
    text = "🏆 **TOP-30 OVOZ YIG'UVCHILAR:**\n\n"
    for idx, row in enumerate(top_list, 1):
        text += f"{idx}. {row['full_name']} [{row['role']}] — **{row['confirmed_count']} ta**\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📑 Pullik agentlar hisoboti (Excel)", F.from_user.id == ADMIN_ID)
async def admin_excel(message: types.Message):
    records = await db.get_paid_agents_report()
    if not records:
        await message.answer("Hisobot uchun ma'lumot topilmadi.")
        return
        
    df = pd.DataFrame([dict(r) for r in records])
    df.columns = ["ID", "Vaqt", "Agent Ismi", "Telefon Raqam", "Status"]
    
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pullik Agentlar")
    buf.seek(0)
    
    file = BufferedInputFile(buf.getvalue(), filename="Pullik_Agentlar_Hisoboti.xlsx")
    await message.answer_document(document=file, caption="📑 Barcha pullik agentlarning tartiblangan hisoboti.")

async def main():
    await db.create_pool()
    await db.init_db()
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())