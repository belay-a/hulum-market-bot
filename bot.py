import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from supabase import create_client

# ==========================================
# 1. ማዋቀር (የራስህን መረጃዎች እዚህ ተካ)
# ==========================================
SUPABASE_URL = "https://lfjkycxbixfknpvxbkim.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxmamt5Y3hiaXhma25wdnhia2ltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5NzQzNTcsImV4cCI6MjA5MjU1MDM1N30.yMj5S1wiI0FReCQKiVFbyAIUthqfeC8U5dfxI9izkc8"
API_TOKEN = '8694072606:AAFDLAJXjMgJQx8QS7ddKu0sdq6hGPyO70U'


# አዲስ የተጨመሩ መረጃዎች
ADMIN_ID = 6929337029 # ⚠️ የራስህን (የአድሚኑን) ቴሌግራም ID ቁጥር እዚህ አስገባ
CHANNEL_ID = "@HuluMarketEthio" # ⚠️ የቻናሉን ዩዘርኔም አስገባ (ቦቱ የቻናሉ አድሚን መሆን አለበት)


logging.basicConfig(level=logging.INFO)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==========================================
# 2. የዕቃ ዘርፎች (Categories) ዝርዝር
# ==========================================
CATEGORIES = [
    "1. ኤሌክትሮኒክስ (Electronics)",
    "2. የቤት ውስጥ እቃዎችና ፈርኒቸር (Home & Furniture)",
    "3. የቤት ውስጥ የኤሌክትሪክ እቃዎች (Home Appliances)",
    "4. አልባሳትና ጫማዎች (Clothing & Apparel)",
    "5. የምግብና የመጠጥ እቃዎች (Groceries & Beverages)",
    "6. የውበትና የጤና መጠበቂያዎች (Health & Beauty)",
    "7. የስፖርትና የውጪ መዝናኛ እቃዎች (Sports & Outdoors)",
    "8. የህፃናት እቃዎች (Baby Products)"
]

def get_categories_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=CATEGORIES[0]), KeyboardButton(text=CATEGORIES[1])],
        [KeyboardButton(text=CATEGORIES[2]), KeyboardButton(text=CATEGORIES[3])],
        [KeyboardButton(text=CATEGORIES[4]), KeyboardButton(text=CATEGORIES[5])],
        [KeyboardButton(text=CATEGORIES[6]), KeyboardButton(text=CATEGORIES[7])]
    ], resize_keyboard=True)

# ==========================================
# 3. የሁኔታዎች (States) መግለጫ
# ==========================================
class Registration(StatesGroup):
    merchant_name = State()
    region = State()
    zone = State()
    woreda = State()
    kebele = State()

class ProductForm(StatesGroup):
    category = State()
    product_name = State()
    description = State() # 🆕 ስለ ዕቃው ማብራሪያ ተጨምሯል
    price = State()
    photo = State()

class BuyerFilter(StatesGroup):
    category = State()
    region = State()
    zone = State()
    woreda = State()
    kebele = State()

class EditProfile(StatesGroup):
    merchant_name = State()
    phone = State()  # 🆕 አዲስ ስቴት
    region = State()
    zone = State()
    woreda = State()
    kebele = State()

class EditProduct(StatesGroup):
    price = State()

class PaymentState(StatesGroup):
    receipt_photo = State()

# ==========================================
# 4. ዋና የኪቦርድ አዝራሮች
# ==========================================
kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="ሁሉንም ዕቃዎች ይመልከቱ"), KeyboardButton(text="በአድራሻ ፈልግ")],
    [KeyboardButton(text="ዕቃ ለመመዝገብ /add"), KeyboardButton(text="የእኔ ዕቃዎች (ማስተካከያ)")],
    [KeyboardButton(text="🚀 ዕቃዎችን ወደ ቻናል ላክ"), KeyboardButton(text="ፕሮፋይል ማስተካከያ")]
], resize_keyboard=True)

def get_edit_delete_kb(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ዋጋ አስተካክል", callback_data=f"edit_price_{product_id}")],
        [InlineKeyboardButton(text="🗑 ሰርዝ", callback_data=f"del_{product_id}")]
    ])

# ==========================================
# 5. መነሻ እና ዕቃ ማየት
# ==========================================
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("እንኳን ደህና መጡ! ምን ማድረግ ይፈልጋሉ?", reply_markup=kb)

@dp.message(F.text == "ሁሉንም ዕቃዎች ይመልከቱ")
async def show_items(message: types.Message):
    try:
        res = supabase.table("products").select("*, merchants(*)").execute()
        items = res.data
        if not items:
            await message.answer("በአሁኑ ሰዓት ምንም ዕቃ አልተመዘገበም!")
            return
        for item in items:
            m = item.get('merchants')
            if m:
                desc = item.get('description', '')
                desc_text = f"\n📝 መግለጫ: {desc}" if desc else ""
                caption = f"🏷 ዘርፍ: {item.get('category', 'ያልታወቀ')}\n📦 ምርት: {item['product_name']}{desc_text}\n💰 ዋጋ: {item['price']} ብር\n📍 አድራሻ: {m['region']}፣ {m['zone']}፣ {m['woreda']}፣ ቀበሌ {m['kebele']}\n🏢 ነጋዴ: {m['merchant_name']}"
                await message.answer_photo(photo=item['image_url'], caption=caption)
    except Exception as e:
        await message.answer("❌ መረጃዎችን ማምጣት አልተቻለም!")

# ==========================================
# 6. የዕቃ ምዝገባ (ማብራሪያን ጨምሮ)
# ==========================================
@dp.message(Command("add"))
@dp.message(F.text == "ዕቃ ለመመዝገብ /add")
async def add_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        res = supabase.table("merchants").select("*").eq("id", user_id).execute()
        if not res.data:
            await state.set_state(Registration.merchant_name)
            await message.answer("ለመጀመሪያ ጊዜ ሲጠቀሙ መመዝገብ ይኖርብዎታል። እባክዎ የሱቅዎን ስም ይጻፉ፦", reply_markup=ReplyKeyboardRemove())
        else:
            await state.set_state(ProductForm.category)
            await message.answer("እባክዎ የሚሸጡትን ዕቃ ዘርፍ ከታች ካሉት አማራጮች ይምረጡ፦", reply_markup=get_categories_kb())
    except Exception as e:
        await message.answer("❌ ከዳታቤዝ ጋር መገናኘት አልተቻለም!")

@dp.message(Registration.merchant_name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(merchant_name=message.text)
    await state.set_state(Registration.phone) # ቀጣይ ስልክ ቁጥር
    await message.answer("ስልክ ቁጥርዎን ያስገቡ:")

@dp.message(Registration.phone) # 🆕 ስልክ ቁጥር መቀበያ
async def reg_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Registration.region)
    await message.answer("ክልልዎን ይጻፉ፦")

@dp.message(Registration.region)
async def reg_region(message: types.Message, state: FSMContext):
    await state.update_data(region=message.text)
    await state.set_state(Registration.zone)
    await message.answer("ዞንዎን ይጻፉ፦")

@dp.message(Registration.zone)
async def reg_zone(message: types.Message, state: FSMContext):
    await state.update_data(zone=message.text)
    await state.set_state(Registration.woreda)
    await message.answer("ወረዳዎን ይጻፉ፦")

@dp.message(Registration.woreda)
async def reg_woreda(message: types.Message, state: FSMContext):
    await state.update_data(woreda=message.text)
    await state.set_state(Registration.kebele)
    await message.answer("ቀበሌ ወይም ሰፈርዎን ይጻፉ፦")

@dp.message(Registration.kebele)
async def reg_kebele(message: types.Message, state: FSMContext):
    data = await state.get_data()
    merchant_data = {
        "id": message.from_user.id,
        "merchant_name": data['merchant_name'],
        "phone": data['phone'],        # 🆕 ስልክ ቁጥር ከዳታ ተወሰደ
        "region": data['region'],
        "zone": data['zone'],
        "woreda": data['woreda'],
        "kebele": message.text,
        "is_paid": False
    }
    try:
        supabase.table("merchants").insert(merchant_data).execute()
        await state.set_state(ProductForm.category)
        await message.answer("🎉 ምዝገባዎ ተጠናቋል! አሁን የሚሸጡትን የዕቃ ዘርፍ ከታች ይምረጡ፦", reply_markup=get_categories_kb())
    except Exception as e:
        await message.answer("❌ መረጃዎን መመዝገብ አልተቻለም!", reply_markup=kb)
        await state.clear()
@dp.message(ProductForm.category)
async def prod_category(message: types.Message, state: FSMContext):
    if message.text not in CATEGORIES:
        await message.answer("እባክዎ ዘርፉን ከታች ከቀረቡት አዝራሮች በመጫን ብቻ ይምረጡ!")
        return
    await state.update_data(category=message.text)
    await state.set_state(ProductForm.product_name)
    await message.answer("የሚሸጡትን የዕቃ ስም ይጻፉ፦", reply_markup=ReplyKeyboardRemove())

@dp.message(ProductForm.product_name)
async def prod_name(message: types.Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await state.set_state(ProductForm.description)
    # 🆕 ማብራሪያ መጠየቅ
    await message.answer("ስለ ዕቃው ማብራሪያ (Description) ይጻፉ፦\n(ለምሳሌ፡ ከለር፣ ሳይዝ፣ ጥራት...)")

@dp.message(ProductForm.description)
async def prod_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ProductForm.price)
    await message.answer("የዕቃውን ዋጋ በብር ይጻፉ፦")

@dp.message(ProductForm.price)
async def prod_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(ProductForm.photo)
    await message.answer("የዕቃውን ፎቶ (Image) ይላኩ፦")

@dp.message(ProductForm.photo, F.photo)
async def prod_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    merchant_id = message.from_user.id
    
    product_data = {
        "merchant_id": merchant_id,
        "category": data['category'],
        "product_name": data['product_name'],
        "description": data['description'], 
        "price": data['price'],
        "image_url": photo_id
    }
    try:
        supabase.table("products").insert(product_data).execute()
        await message.answer("✅ ዕቃዎ በተሳካ ሁኔታ ተመዝግቧል።", reply_markup=kb)
        
        # የነጋዴውን መረጃ ከስልክ ቁጥሩ ጋር መሳብ
        m_res = supabase.table("merchants").select("*").eq("id", merchant_id).execute()
        
        if m_res.data and m_res.data[0].get('is_paid'):
            m = m_res.data[0]
            desc = data['description']
            phone = m.get('phone', 'ስልክ አልተመዘገበም') # 🆕 ስልኩን ከዳታቤዝ መውሰድ
            
            caption = (
                f"🆕 አዲስ ዕቃ ተጨመረ!\n\n"
                f"🏷 ዘርፍ: {data['category']}\n"
                f"📦 ምርት: {data['product_name']}\n"
                f"📝 መግለጫ: {desc}\n"
                f"💰 ዋጋ: {data['price']} ብር\n"
                f"📞 ስልክ: {phone}\n" # 🆕 ስልክ ቁጥር እዚህ ተጨመረ
                f"📍 አድራሻ: {m['region']}፣ {m['zone']}\n"
                f"🏢 ሱቅ: {m['merchant_name']}"
            )
            await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=caption)
            
        await state.clear()
    except Exception as e:
        await message.answer("❌ ዕቃውን መመዝገብ አልተቻለም!", reply_markup=kb)

# ==========================================
# 7. ፕሮፋይል ማስተካከያ (ሙሉ አድራሻ እና ስልክ)
# ==========================================
@dp.message(F.text == "ፕሮፋይል ማስተካከያ")
async def edit_profile_start(message: types.Message, state: FSMContext):
    try:
        res = supabase.table("merchants").select("*").eq("id", message.from_user.id).execute()
        if not res.data:
            await message.answer("❌ መጀመሪያ ይመዝገቡ።")
            return
        
        user_data = res.data[0]
        # ያሉትን መረጃዎች state ላይ እናስቀምጣለን
        await state.update_data(
            cur_name=user_data['merchant_name'],
            cur_phone=user_data.get('phone', 'N/A'), # 🆕 ስልክ ቁጥር ተያዘ
            cur_reg=user_data['region'],
            cur_zone=user_data['zone'],
            cur_wor=user_data['woreda'],
            cur_keb=user_data['kebele']
        )
        
        await state.set_state(EditProfile.merchant_name)
        await message.answer(
            f"🛠 **ፕሮፋይል ማስተካከያ**\nማስተካከል የማይፈልጉትን መረጃ ለማለፍ ነጥብ (`.`) ብቻ ይላኩ።\n\n"
            f"የአሁኑ የሱቅ ስም: **{user_data['merchant_name']}**\nአዲሱን የሱቅ ስም ይጻፉ፦", 
            reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer("❌ ችግር አጋጥሟል!")

@dp.message(EditProfile.merchant_name)
async def edit_prof_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_name = message.text if message.text != "." else data['cur_name']
    await state.update_data(merchant_name=new_name)
    
    await state.set_state(EditProfile.phone) # 🆕 ወደ ስልክ ስቴት
    await message.answer(f"የአሁኑ ስልክ: **{data['cur_phone']}**\nአዲሱን ስልክ ቁጥር ይጻፉ (ለማለፍ `.` ይላኩ)፦", parse_mode="Markdown")

@dp.message(EditProfile.phone)
async def edit_prof_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_phone = message.text if message.text != "." else data['cur_phone']
    await state.update_data(phone=new_phone)
    
    await state.set_state(EditProfile.region)
    await message.answer(f"የአሁኑ ክልል: **{data['cur_reg']}**\nአዲሱን ክልል ይጻፉ (ለማለፍ `.` ይላኩ)፦", parse_mode="Markdown")

@dp.message(EditProfile.region)
async def edit_prof_region(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_reg = message.text if message.text != "." else data['cur_reg']
    await state.update_data(region=new_reg)
    
    await state.set_state(EditProfile.zone)
    await message.answer(f"የአሁኑ ዞን: **{data['cur_zone']}**\nአዲሱን ዞን ይጻፉ (ለማለፍ `.` ይላኩ)፦", parse_mode="Markdown")

@dp.message(EditProfile.zone)
async def edit_prof_zone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_zone = message.text if message.text != "." else data['cur_zone']
    await state.update_data(zone=new_zone)
    
    await state.set_state(EditProfile.woreda)
    await message.answer(f"የአሁኑ ወረዳ: **{data['cur_wor']}**\nአዲሱን ወረዳ ይጻፉ (ለማለፍ `.` ይላኩ)፦", parse_mode="Markdown")

@dp.message(EditProfile.woreda)
async def edit_prof_woreda(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_wor = message.text if message.text != "." else data['cur_wor']
    await state.update_data(woreda=new_wor)
    
    await state.set_state(EditProfile.kebele)
    await message.answer(f"የአሁኑ ቀበሌ: **{data['cur_keb']}**\nአዲሱን ቀበሌ ይጻፉ (ለማለፍ `.` ይላኩ)፦", parse_mode="Markdown")

@dp.message(EditProfile.kebele)
async def edit_prof_kebele(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_keb = message.text if message.text != "." else data['cur_keb']
    
    update_data = {
        "merchant_name": data['merchant_name'],
        "phone": data['phone'], # 🆕 አዲሱ ስልክ ቁጥር
        "region": data['region'],
        "zone": data['zone'],
        "woreda": data['woreda'],
        "kebele": new_keb
    }
    
    try:
        supabase.table("merchants").update(update_data).eq("id", message.from_user.id).execute()
        await message.answer("✅ ፕሮፋይልዎ፣ ስልክ ቁጥርዎ እና አድራሻዎ በተሳካ ሁኔታ ተስተካክሏል!", reply_markup=kb)
    except Exception as e:
        await message.answer("❌ ማስተካከል አልተሳካም።", reply_markup=kb)
    await state.clear()
# ==========================================
#@dp.message(BuyerFilter.woreda)
async def filter_woreda(message: types.Message, state: FSMContext):
    woreda = message.text
    data = await state.get_data()
    selected_category = data['category']
    
    try:
        # 1. በወረዳ የተመዘገቡ ነጋዴዎችን መፈለግ
        merchants_res = supabase.table("merchants").select("*").ilike("woreda", f"%{woreda}%").execute()
        
        if not merchants_res.data:
            await message.answer(f"❌ በወረዳ '{woreda}' የተመዘገበ ነጋዴ የለም።", reply_markup=kb)
            await state.clear()
            return
            
        merchant_ids = [m['id'] for m in merchants_res.data]
        
        # 2. የእነዚህ ነጋዴዎች ምርቶች በዘርፍ መፈለግ
        products_res = supabase.table("products").select("*").in_("merchant_id", merchant_ids).eq("category", selected_category).execute()
        
        if not products_res.data:
            await message.answer(f"❌ በዚህ ወረዳ የ **{selected_category}** ዘርፍ ዕቃ አልተገኘም።", reply_markup=kb)
            await state.clear()
            return
            
        merchants_dict = {m['id']: m for m in merchants_res.data}
        await message.answer(f"✅ {len(products_res.data)} ዕቃዎች ተገኝተዋል፡", reply_markup=kb)
        
        # 3. ዕቃዎችን ከነ ሙሉ ፕሮፋይላቸው ማሳየት
        for item in products_res.data:
            m = merchants_dict.get(item['merchant_id'])
            
            # የነጋዴውን ሙሉ ፕሮፋይል መረጃ ማዘጋጀት
            merchant_name = m.get('merchant_name', 'ያልታወቀ')
            phone = m.get('phone', 'ስልክ ቁጥር የለም')
            region = m.get('region', 'ያልተገለጸ')
            zone = m.get('zone', 'ያልተገለጸ')
            woreda_val = m.get('woreda', 'ያልተገለጸ')
            kebele = m.get('kebele', 'ያልተገለጸ')
            
            desc = item.get('description', '')
            desc_text = f"\n📝 መግለጫ: {desc}" if desc else ""
            
            # ሙሉ ፕሮፋይል እና የዕቃ መረጃን የያዘ caption
            caption = (
                f"🏷 ዘርፍ: {item.get('category', '')}\n"
                f"📦 ምርት: {item['product_name']}{desc_text}\n"
                f"💰 ዋጋ: {item['price']} ብር\n\n"
                f"👤 ነጋዴው: {merchant_name}\n"
                f"📞 ስልክ: {phone}\n"
                f"📍 አድራሻ: {region}፣ {zone}፣ {woreda_val}፣ {kebele}"
            )
            await message.answer_photo(photo=item['image_url'], caption=caption)
            
    except Exception as e:
        await message.answer("❌ ችግር አጋጥሟል!", reply_markup=kb)
    await state.clear()

# ==========================================
# 9. የዕቃ ማስተካከያ እና መሰረዝ
# ==========================================
@dp.message(F.text == "የእኔ ዕቃዎች (ማስተካከያ)")
async def show_my_items(message: types.Message):
    user_id = message.from_user.id
    try:
        res = supabase.table("products").select("*").eq("merchant_id", user_id).execute()
        items = res.data
        if not items:
            await message.answer("እርስዎ እስካሁን ምንም ዕቃ አልመዘገቡም!")
            return
        await message.answer("የእርስዎ ዕቃዎች ዝርዝር፦")
        for item in items:
            desc = item.get('description', '')
            desc_text = f"\n📝 መግለጫ: {desc}" if desc else ""
            caption = f"🏷 ዘርፍ: {item.get('category', '')}\n📦 ምርት: {item['product_name']}{desc_text}\n💰 ዋጋ: {item['price']} ብር"
            await message.answer_photo(photo=item['image_url'], caption=caption, reply_markup=get_edit_delete_kb(item['id']))
    except Exception as e:
        await message.answer("❌ ዕቃዎችዎን ማምጣት አልተቻለም!")

@dp.callback_query(F.data.startswith("del_"))
async def delete_product(callback: types.CallbackQuery):
    product_id = callback.data.split("_")[1]
    try:
        supabase.table("products").delete().eq("id", product_id).execute()
        await callback.message.delete()
        await callback.answer("✅ ዕቃው ተሰርዟል!", show_alert=True)
    except Exception as e:
        await callback.answer("❌ መሰረዝ አልተቻለም!", show_alert=True)

@dp.callback_query(F.data.startswith("edit_price_"))
async def edit_product_price(callback: types.CallbackQuery, state: FSMContext):
    product_id = callback.data.split("_")[2]
    await state.update_data(edit_product_id=product_id)
    await state.set_state(EditProduct.price)
    await callback.message.answer("እባክዎ ለዚህ ዕቃ አዲሱን ዋጋ በብር ይጻፉ፦")
    await callback.answer()

@dp.message(EditProduct.price)
async def save_new_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("edit_product_id")
    new_price = message.text
    merchant_id = message.from_user.id
    try:
        supabase.table("products").update({"price": new_price}).eq("id", product_id).execute()
        await message.answer("✅ የዕቃው ዋጋ ተስተካክሏል!", reply_markup=kb)
        
        m_res = supabase.table("merchants").select("*").eq("id", merchant_id).execute()
        p_res = supabase.table("products").select("*").eq("id", product_id).execute()
        if m_res.data and m_res.data[0].get('is_paid') and p_res.data:
            m = m_res.data[0]
            p = p_res.data[0]
            desc = p.get('description', '')
            desc_text = f"\n📝 መግለጫ: {desc}" if desc else ""
            caption = f"🔄 ዋጋ ተሻሽሏል!\n\n🏷 ዘርፍ: {p.get('category', '')}\n📦 ምርት: {p['product_name']}{desc_text}\n💰 አዲስ ዋጋ: {new_price} ብር\n📍 አድራሻ: {m['region']}፣ {m['zone']}\n🏢 ሱቅ: {m['merchant_name']}"
            await bot.send_photo(chat_id=CHANNEL_ID, photo=p['image_url'], caption=caption)
    except Exception as e:
        await message.answer("❌ ዋጋውን ማስተካከል አልተቻለም።", reply_markup=kb)
    await state.clear()

# ==========================================
# 10. ክፍያ እና አውቶማቲክ ፖስት (Cron Job)
# ==========================================
@dp.message(F.text == "🚀 ዕቃዎችን ወደ ቻናል ላክ")
async def start_payment_process(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        res = supabase.table("products").select("*").eq("merchant_id", user_id).execute()
        if not res.data:
            await message.answer("❌ ወደ ቻናል ከመላክዎ በፊት እባክዎ ቢያንስ አንድ ዕቃ ይመዝግቡ።")
            return
    except Exception as e:
         await message.answer("❌ ችግር አጋጥሟል!")
         return
         
    await state.set_state(PaymentState.receipt_photo)
    payment_info = (
        "🌟 **ዕቃዎችዎን በየቀኑ አውቶማቲካሊ ቻናላችን ላይ ለመልቀቅ**\n\n"
        "ክፍያ: **200 ብር (ለ1 ሙሉ ወር)**\n"
        "የቴሌብር ቁጥር: `0989272770`\n\n"
        "📌 ክፍያውን እንደፈጸሙ የደረሰኙን ፎቶ አሁን እዚህ ይላኩ።"
    )
    await message.answer(payment_info, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

@dp.message(PaymentState.receipt_photo, F.photo)
async def receive_receipt(message: types.Message, state: FSMContext):
    merchant_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"approve_{merchant_id}")],
        [InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{merchant_id}")]
    ])
    caption = f"🔔 **አዲስ የክፍያ ጥያቄ**\n\nየነጋዴ ID: `{merchant_id}`"
    try:
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption, reply_markup=admin_kb)
        await message.answer("✅ ደረሰኝዎ ለአድሚን ተልኳል። ሲረጋገጥ ዕቃዎችዎ በየቀኑ ወደ ቻናል መለቀቅ ይጀምራሉ!", reply_markup=kb)
    except Exception as e:
        await message.answer("❌ መላክ አልተቻለም።", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    merchant_id = int(callback.data.split("_")[1])
    expiry_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
    try:
        supabase.table("merchants").update({"is_paid": True, "expiry_date": expiry_date}).eq("id", merchant_id).execute()
        res = supabase.table("products").select("*, merchants(*)").eq("merchant_id", merchant_id).execute()
        if res.data:
            for item in res.data:
                m = item['merchants']
                desc = item.get('description', '')
                desc_text = f"\n📝 መግለጫ: {desc}" if desc else ""
                caption = f"🏷 ዘርፍ: {item.get('category', '')}\n📦 ምርት: {item['product_name']}{desc_text}\n💰 ዋጋ: {item['price']} ብር\n📍 አድራሻ: {m['region']}፣ {m['zone']}\n🏢 ሱቅ: {m['merchant_name']}"
                await bot.send_photo(chat_id=CHANNEL_ID, photo=item['image_url'], caption=caption)
            await bot.send_message(chat_id=merchant_id, text="🎉 ክፍያዎ ፅድቋል! ዕቃዎችዎ አሁን ወደ ቻናል ተለቀዋል፤ ለሚቀጥሉት 30 ቀናት በየቀኑ አውቶማቲካሊ ይለቀቃሉ።")
            await callback.message.edit_caption(caption=f"✅ የ ID `{merchant_id}` ክፍያ ጸድቋል!")
        else:
            await callback.answer("ነጋዴው ዕቃ አልመዘገበም!", show_alert=True)
    except Exception as e:
        await callback.answer("❌ ስህተት አጋጥሟል!", show_alert=True)

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    merchant_id = int(callback.data.split("_")[1])
    try:
        await bot.send_message(chat_id=merchant_id, text="❌ የላኩት የክፍያ ደረሰኝ አልተረጋገጠም ውድቅ ተደርጓል።")
        await callback.message.edit_caption(caption=f"❌ የ ID `{merchant_id}` ክፍያ ውድቅ ተደርጓል።")
    except Exception as e:
        await callback.answer("ስህተት!")

async def daily_cron_job():
    while True:
        await asyncio.sleep(86400)
        logging.info("የእለቱ አውቶማቲክ የቻናል ፖስት እና የጊዜ ማጣሪያ ተጀምሯል...")
        try:
            res = supabase.table("merchants").select("*").eq("is_paid", True).execute()
            now = datetime.utcnow()
            if res.data:
                for merchant in res.data:
                    merchant_id = merchant['id']
                    expiry_str = merchant.get('expiry_date')
                    if expiry_str:
                        expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        if now >= expiry_date:
                            supabase.table("merchants").update({"is_paid": False}).eq("id", merchant_id).execute()
                            try:
                                await bot.send_message(chat_id=merchant_id, text="⚠️ **የ 1 ወር የቻናል ማስታወቂያ አገልግሎት ጊዜዎ አብቅቷል!**\n\nዕቃዎችዎ በየቀኑ ወደ ቻናል መለጠፋቸው እንዲቀጥል እባክዎ በ '🚀 ዕቃዎችን ወደ ቻናል ላክ' አዝራር በኩል በድጋሚ ክፍያ ይፈጽሙ።")
                            except Exception:
                                pass
                            continue
                        
                        prod_res = supabase.table("products").select("*").eq("merchant_id", merchant_id).execute()
                        if prod_res.data:
                            for item in prod_res.data:
                                desc = item.get('description', '')
                                desc_text = f"\n📝 መግለጫ: {desc}" if desc else ""
                                caption = f"🔄 የእለቱ ምርጥ ዕቃዎች!\n\n🏷 ዘርፍ: {item.get('category', '')}\n📦 ምርት: {item['product_name']}{desc_text}\n💰 ዋጋ: {item['price']} ብር\n📍 አድራሻ: {merchant['region']}፣ {merchant['zone']}\n🏢 ሱቅ: {merchant['merchant_name']}"
                                try:
                                    await bot.send_photo(chat_id=CHANNEL_ID, photo=item['image_url'], caption=caption)
                                    await asyncio.sleep(2)
                                except Exception as e:
                                    pass
        except Exception as e:
            pass

async def main():
    asyncio.create_task(daily_cron_job())
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("ቦት ቆሟል።")
