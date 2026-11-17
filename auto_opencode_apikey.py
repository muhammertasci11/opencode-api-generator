import os
import re
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opencode_api_keys.txt")

def log(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)

def run_automation(headless=False):
    log("Otomasyon başlatılıyor...")
    with sync_playwright() as p:
        # Chromium tarayıcısını başlatıyoruz (kullanıcının süreci izleyebilmesi için varsayılan olarak pencereli)
        browser = p.chromium.launch(
            headless=headless,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )

        # -------------------------------------------------------------
        # ADIM 1: TempMail123 sitesinden geçici e-posta alma
        # -------------------------------------------------------------
        page_mail = context.new_page()
        log("1/5: TempMail123'e gidiliyor...")
        page_mail.goto("https://tempmail123.com", wait_until="domcontentloaded")
        
        log("Geçici e-posta adresi bekleniyor...")
        email = None
        for _ in range(30):
            try:
                # 'mail' id'li input kutusunu kontrol et
                mail_input = page_mail.locator("input#mail")
                if mail_input.count() > 0:
                    val = mail_input.input_value().strip()
                    if val and "@" in val and not val.endswith("..."):
                        email = val
                        break
            except Exception:
                pass
            time.sleep(1)

        if not email:
            # Fallback regex ile sayfadaki ilk maili ara
            content = page_mail.content()
            matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content)
            for m in matches:
                if "tempmail" not in m:
                    email = m
                    break

        if not email:
            log("[-] HATA: Geçici e-posta adresi alınamadı.")
            browser.close()
            return None

        log(f"[+] Alınan E-posta: {email}")

        # -------------------------------------------------------------
        # ADIM 2: OpenCode Console Kayıt (Signup)
        # -------------------------------------------------------------
        page_opencode = context.new_page()
        log("2/5: OpenCode Signup sayfasına gidiliyor...")
        page_opencode.goto("https://opencode.ai/console/signup", wait_until="domcontentloaded")
        page_opencode.wait_for_timeout(2000)

        log("Kayıt formu dolduruluyor (E-posta ve Şifre)...")
        # E-posta kutusu
        email_input = page_opencode.locator("input[type='email']")
        email_input.wait_for(state="visible", timeout=15000)
        email_input.fill(email)

        # Şifre kutusu (şifre ve mail aynı olacak)
        password_input = page_opencode.locator("input[type='password']")
        password_input.wait_for(state="visible", timeout=15000)
        password_input.fill(email)

        page_opencode.wait_for_timeout(1000)

        # 'Create Account' butonuna tıklama
        create_btn = page_opencode.locator("button:has-text('Create Account')")
        create_btn.wait_for(state="visible", timeout=10000)
        create_btn.click()
        log("[+] 'Create Account' butonuna tıklandı.")

        # Sayfanın 'Check your email' aşamasına geçmesini bekle
        page_opencode.wait_for_timeout(3000)

        # -------------------------------------------------------------
        # ADIM 3: TempMail'e gelen doğrulama e-postasını açıp onaylama
        # -------------------------------------------------------------
        log("3/5: TempMail gelen kutusu kontrol ediliyor...")
        page_mail.bring_to_front()

        mail_found = False
        start_wait = time.time()
        # E-postanın gelmesi için 90 saniyeye kadar bekle
        while time.time() - start_wait < 90:
            try:
                # E-posta listesinde 'OpenCode' veya 'Verify your email' metnini ara
                email_row = page_mail.locator("text='OpenCode Console'").or_(page_mail.locator("text='Verify your email'"))
                if email_row.count() > 0 and email_row.first.is_visible():
                    log("[+] Doğrulama e-postası ulaştı! Açılıyor...")
                    email_row.first.click()
                    mail_found = True
                    break
            except Exception:
                pass
            
            # Yenileme butonu varsa tıkla veya bekle
            time.sleep(3)

        if not mail_found:
            log("[-] UYARI: Doğrulama postası zaman aşımına uğradı.")
            log("Lütfen gelen kutusunu kontrol edip elle tıklayınız.")
            page_mail.wait_for_timeout(15000)
        else:
            page_mail.wait_for_timeout(2000)
            # E-posta içindeki doğrulama butonunu/linkini bul
            log("E-posta içerisindeki doğrulama linki aranıyor...")
            verify_link = None
            
            # iframe kontrolü (çoğu temp mail e-posta gövdesini iframe içinde gösterir)
            frames = page_mail.frames
            for frame in frames:
                try:
                    btn = frame.locator("a:has-text('Verify'), a:has-text('Doğrula'), a[href*='verify'], a[href*='confirm']")
                    if btn.count() > 0 and btn.first.is_visible():
                        verify_link = btn.first.get_attribute("href")
                        break
                except Exception:
                    pass

            if not verify_link:
                try:
                    btn = page_mail.locator("a:has-text('Verify'), a:has-text('Doğrula'), a[href*='verify'], a[href*='confirm']")
                    if btn.count() > 0:
                        verify_link = btn.first.get_attribute("href")
                except Exception:
                    pass

            if verify_link:
                log(f"[+] Doğrulama linki bulundu: {verify_link[:50]}...")
                page_opencode.bring_to_front()
                page_opencode.goto(verify_link, wait_until="domcontentloaded")
            else:
                log("[*] Doğrulama linkine doğrudan tıklanıyor...")
                try:
                    page_mail.locator("a:has-text('Verify'), a:has-text('Sign In'), a:has-text('OpenCode')").first.click()
                except Exception as e:
                    log(f"[-] Linke tıklanamadı: {e}")

        # -------------------------------------------------------------
        # ADIM 4: OpenCode Konsoluna Giriş ve Settings -> Account Sayfası
        # -------------------------------------------------------------
        page_opencode.bring_to_front()
        log("4/5: Konsol paneli yükleniyor...")
        page_opencode.wait_for_timeout(5000)

        # Settings sayfasına git
        current_url = page_opencode.url
        log(f"Mevcut URL: {current_url}")
        
        # 'Settings' menüsüne tıkla veya doğrudan URL'e git
        try:
            settings_link = page_opencode.locator("text='Settings'").first
            if settings_link.is_visible():
                settings_link.click()
                page_opencode.wait_for_timeout(2000)
        except Exception:
            pass

        # 'Personal' altındaki 'Account' linkine tıkla
        try:
            account_link = page_opencode.locator("text='Account'").first
            if account_link.is_visible():
                account_link.click()
                page_opencode.wait_for_timeout(2000)
        except Exception:
            pass

        # -------------------------------------------------------------
        # ADIM 5: Sınırsız Süreli (Never) Full Access API Key Oluşturma
        # -------------------------------------------------------------
        log("5/5: 'Add API key' butonu aranıyor...")
        add_key_btn = page_opencode.locator("button:has-text('Add API key')").or_(page_opencode.locator("button:has-text('Create API key')"))
        
        try:
            add_key_btn.wait_for(state="visible", timeout=15000)
            add_key_btn.first.click()
            log("[+] 'Add API key' tıklandı.")
        except Exception as e:
            log(f"[-] 'Add API key' butonu bulunamadı, lütfen ekrandan kontrol ediniz: {e}")

        page_opencode.wait_for_timeout(2000)

        # Modal içi alanlar
        # 1. Key name
        try:
            key_name_input = page_opencode.locator("input[placeholder*='name'], input[placeholder*='Key'], div[role='dialog'] input").first
            key_name_input.fill(f"key-{int(time.time())}")
            log("[+] Key name girildi.")
        except Exception as e:
            log(f"Key name alanı doldurulamadı: {e}")

        # 2. Expiration -> Kesinlikle '90 days' kutusunu açıp 'Never' seçimi
        log("Expiration seçeneği 'Never' (Sınırsız) olarak ayarlanıyor...")
        try:
            # 90 days açılır menü kutusunu bul ve tıkla
            exp_box = (
                page_opencode.locator("text='90 days'")
                .or_(page_opencode.locator("*:has-text('90 days')").last)
                .or_(page_opencode.locator("xpath=//*[text()='Expiration']/following::*[contains(text(), '90')][1]"))
                .or_(page_opencode.locator("xpath=//*[text()='Expiration']/following::*[contains(text(), 'days')][1]"))
                .or_(page_opencode.locator("button:has-text('days'), div:has-text('days')").first)
            ).first

            if exp_box.is_visible():
                log(f"[+] '{exp_box.inner_text().strip()}' kutusu bulundu, tıklanıyor...")
                exp_box.click(force=True)
                page_opencode.wait_for_timeout(800)

                # Açılan listede en üstte yer alan 'Never' seçeneğine tıkla
                never_opt = (
                    page_opencode.locator("text='Never'").first
                    .or_(page_opencode.locator("[role='option']:has-text('Never')").first)
                    .or_(page_opencode.locator("div:text-is('Never')").first)
                ).first

                if never_opt.is_visible():
                    never_opt.click(force=True)
                    page_opencode.wait_for_timeout(800)
                    log("[+] 'Never' seçeneği başarıyla tıklandı ve seçildi!")
                else:
                    log("[-] Açılan menüde 'Never' görünür bulunamadı.")
            else:
                log("[-] '90 days' kutusu bulunamadı, doğrudan 'Never' aranıyor...")
                page_opencode.locator("text='Never'").first.click(force=True)
        except Exception as e:
            log(f"[-] Expiration seçimi sırasında hata: {e}")

        # 3. Permissions -> Kesinlikle 'Full access' seçimi
        try:
            full_acc_btn = (
                page_opencode.locator("text='Full access'")
                .or_(page_opencode.locator("button:has-text('Full access')"))
                .or_(page_opencode.locator("div[role='radio']:has-text('Full access')"))
            ).first
            
            if full_acc_btn.is_visible():
                full_acc_btn.click(force=True)
                page_opencode.wait_for_timeout(500)
                log("[+] Permissions: 'Full access' seçildi.")
            else:
                log("[-] 'Full access' butonu görünür bulunamadı.")
        except Exception as e:
            log(f"[-] Permissions 'Full access' seçilemedi: {e}")

        page_opencode.wait_for_timeout(500)

        # 4. Create butonu
        try:
            modal_create_btn = page_opencode.locator("div[role='dialog'] button:has-text('Create')").or_(page_opencode.locator("button:has-text('Create')").last)
            modal_create_btn.click()
            log("[+] Modal 'Create' butonuna tıklandı.")
        except Exception as e:
            log(f"Modal Create butonuna tıklanamadı: {e}")

        page_opencode.wait_for_timeout(3000)

        # -------------------------------------------------------------
        # API Anahtarını Okuma ve Dosyaya Kaydetme
        # -------------------------------------------------------------
        log("Oluşturulan API anahtarı okunuyor...")
        api_key = None

        # 1. Input veya diyalog elemanından tam anahtarı oku
        try:
            key_input = page_opencode.locator("input[value*='oc_sk_'], div[role='dialog'] input, div[role='dialog'] code").first
            if key_input.count() > 0:
                val = key_input.input_value() if key_input.get_attribute("value") is not None else key_input.inner_text()
                if "oc_sk_" in val:
                    api_key = val.strip()
        except Exception:
            pass

        # 2. Sayfa içeriğinden en uzun eşleşen tam anahtarı al
        try:
            dialog_text = page_opencode.content()
            key_matches = re.findall(r'oc_sk_[a-zA-Z0-9_-]+', dialog_text)
            if key_matches:
                longest_match = max(key_matches, key=len)
                if not api_key or len(longest_match) > len(api_key):
                    api_key = longest_match
        except Exception:
            pass

        if api_key:
            log(f"==================================================")
            log(f"BAŞARILI! Yeni API Key: {api_key}")
            log(f"==================================================")

            # Sadece API anahtarını doğrudan alt satıra kaydet
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{api_key}\n")
            log(f"[+] API anahtarı sadece anahtar formatında kaydedildi: {OUTPUT_FILE}")
        else:
            log("[-] API anahtarı otomatik okunamadı, lütfen açık tarayıcı penceresinden anahtarı kopyalayınız.")

        # İşlem tamamlandıktan sonra 3 saniye bekle ve tarayıcıyı kapat
        log("İşlem tamamlandı, tarayıcı 3 saniye içinde kapatılıyor...")
        time.sleep(3)
        browser.close()
        return api_key

if __name__ == "__main__":
    is_headless = "--headless" in sys.argv
    run_automation(headless=is_headless)
