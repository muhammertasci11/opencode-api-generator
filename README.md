# OpenCode Auto API Key Generator

Bu araç, **OpenCode Console** üzerinde otomatik olarak geçici e-posta ile hesap açıp sınırsız süreli (**Never**) ve tam yetkili (**Full Access**) API anahtarı üreten bir Playwright otomasyonudur.

## Özellikler

- **Geçici E-Posta Entegrasyonu:** `tempmail123.com` üzerinden tek kullanımlık e-posta alır.
- **Otomatik Kayıt:** OpenCode üzerinde otomatik kayıt formunu doldurur.
- **Otomatik E-Posta Doğrulama:** Gelen onay e-postasındaki doğrulama bağlantısına tıklar.
- **Sınırsız API Anahtarı:** Konsol ayarlarından `Expiration: Never` ve `Permissions: Full access` seçerek API anahtarı üretir.
- **Temiz Kayıt:** Üretilen anahtarları yerel olarak `opencode_api_keys.txt` dosyasına alt alta kaydeder.
- **Güvenlik:** Üretilen API anahtarları `.gitignore` ile korunur ve kesinlikle git geçmişine eklenmez.

## Kurulum

1. Depoyu klonlayın:
```bash
git clone https://github.com/muhammertasci11/opencode-api-generator.git
cd opencode-api-generator
```

2. Gereksinimleri yükleyin:
```bash
pip install -r requirements.txt
playwright install chromium
```

## Kullanım

### Yöntem 1: Çift Tıklayarak (Windows)
Klasördeki `OpenCode_API_Uret.bat` dosyasına çift tıklayarak çalıştırabilirsiniz. İşlem tamamlandığında terminal 3 saniye sonra otomatik kapanacaktır.

### Yöntem 2: Terminalden
```bash
# Görünür tarayıcı ile çalıştırmak için:
python auto_opencode_apikey.py

# Arka planda (sessiz/headless) çalıştırmak için:
python auto_opencode_apikey.py --headless
```

Üretilen tüm API anahtarları `opencode_api_keys.txt` dosyasında saklanır.
