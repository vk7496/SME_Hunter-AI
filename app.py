import streamlit as st
import pandas as pd
import instaloader
import time
import re

# تنظیمات صفحه استریم‌لایت
st.set_page_config(
    page_title="SME Lead Finder Agent",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 ایجنت هوشمند صید لیدهای SME برای کوچینگ")
st.caption("سیستم خودکار استخراج و فیلتر صاحبان کسب‌وکار از کامنت‌های اینستاگرام")

# نوار کناری تنظیمات
st.sidebar.header("🔑 تنظیمات اتصال اینستاگرام")
st.sidebar.warning("پیشنهاد: حتماً با یک اکانت زاپاس و غیرمهم لاگین کنید.")

ig_username = st.sidebar.text_input("نام کاربری (Username):")
ig_password = st.sidebar.text_input("رمز عبور (Password):", type="password")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ تنظیمات فیلتر هوشمند SMEها")

target_accounts = st.sidebar.text_area(
    "آیدی پیج‌های هدف (هر خط یک آیدی بدون @):",
    value="karnakon\nhosseintaheri\nvahid.hajizadeh\nrehnavard.mg",
    height=100
)

# کلمات کلیدی کاملاً بهینه‌شده برای ۵ حوزه SME و عناوین مدیریتی
default_keywords = (
    "آژانس, دیجیتال مارکتینگ, سئو, آژانس تبلیغاتی, مارکتور, "
    "فروشگاه اینترنتی, برند پوشاک, فروشگاه آنلاین, ای‌کامرس, آنلاین‌شاپ, "
    "معمار, استودیو معماری, طراحی داخلی, معمار داخلی, پروژه ساختمانی, "
    "استارتاپ, نرم‌افزار, SaaS, مدیر محصول, اتوماسیون, "
    "کافه, رستوران, شعبه, فست‌فود, مجموعه غذایی, "
    "مدیر, موسس, بنیانگذار, مدیرعامل"
)

keywords_input = st.sidebar.text_area(
    "کلمات کلیدی فیلتر (شناسایی صاحبان بیزینس):",
    value=default_keywords,
    height=130
)

posts_limit = st.sidebar.slider("تعداد آخرین پست‌های بررسی‌شونده از هر پیج:", 1, 5, 2)
max_comments_per_post = st.sidebar.number_input("حداکثر کامنت‌های بررسی در هر پست:", value=50, step=25)

# تابع اصلی استخراج و فیلتر
def fetch_sme_leads(username, password, targets, keywords, p_limit, c_limit):
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=True,
        save_metadata=False
    )
    
    if username and password:
        try:
            L.login(username, password)
            st.sidebar.success("اتصال موفق به اینستاگرام! ✅")
        except Exception as e:
            st.error(f"خطا در ورود به اینستاگرام: {e}")
            return pd.DataFrame()
    else:
        st.warning("⚠️ بدون لاگین، دسترسی به کامنت‌ها ممکن است توسط اینستاگرام محدود شود.")

    leads = []
    # ساخت الگوی جستجوی هوشمند کلمات کلیدی
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    kw_pattern = re.compile("|".join(kw_list), re.IGNORECASE)

    progress_bar = st.progress(0)
    total_targets = len(targets)

    for idx, target_id in enumerate(targets):
        st.info(f"🔍 در حال اسکن و تحلیل پیج: **@{target_id}**...")
        try:
            profile = instaloader.Profile.from_username(L.context, target_id)
            
            for post_idx, post in enumerate(profile.get_posts()):
                if post_idx >= p_limit:
                    break
                
                comment_count = 0
                for comment in post.get_comments():
                    if comment_count >= c_limit:
                        break
                    
                    comment_text = comment.text
                    commenter = comment.owner
                    
                    try:
                        user_bio = commenter.biography if commenter.biography else ""
                    except Exception:
                        user_bio = ""
                    
                    # بررسی تطابق کلمات کلیدی در متن کامنت یا بیو کاربر
                    combined_text = f"{comment_text} {user_bio}"
                    
                    if kw_pattern.search(combined_text):
                        leads.append({
                            "آیدی کاربر": f"@{commenter.username}",
                            "نام": commenter.full_name,
                            "متن کامنت": comment_text,
                            "بیو (Bio)": user_bio,
                            "تعداد فالوور": getattr(commenter, 'followers', 'نامشخص'),
                            "پیج منبع": f"@{target_id}",
                            "لینک پست": f"https://instagram.com/p/{post.shortcode}/"
                        })
                    
                    comment_count += 1
                    time.sleep(0.2) # تاخیر ایمن برای جلوگیری از محدودیت نرخ اینستاگرام
                    
        except Exception as e:
            st.error(f"خطا در پردازش پیج @{target_id}: {e}")
            
        progress_bar.progress((idx + 1) / total_targets)

    return pd.DataFrame(leads)

# دکمه اجرای ایجنت
if st.button("🚀 شروع فرآیند شکار لیدهای SME"):
    targets_list = [t.strip() for t in target_accounts.split("\n") if t.strip()]
    
    if not targets_list:
        st.error("لطفاً حداقل یک آیدی پیج هدف وارد کنید.")
    else:
        with st.spinner("ایجنت در حال کاوش و فیلتر هوشمند است... لطفاً صبور باشید ⏳"):
            df_result = fetch_sme_leads(
                ig_username, ig_password, targets_list, keywords_input, posts_limit, max_comments_per_post
            )
            
            if not df_result.empty:
                st.success(f"🎉 موفقیت! تعداد {len(df_result)} لید مرتبط با حوزه SME شناسایی شد.")
                
                # نمایش جدول زنده لیدها
                st.dataframe(df_result, use_container_width=True)
                
                # دکمه دانلود خروجی اکسل برای تیم فروش
                csv_data = df_result.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 دانلود فایل اکسل نهایی (CSV)",
                    data=csv_data,
                    file_name="sme_coaching_leads.csv",
                    mime="text/csv"
                )
            else:
                st.warning("هیچ لیدی با این کلمات کلیدی در پست‌های اخیر یافت نشد. پیج‌های هدف یا کلمات را بازبینی کنید.")
