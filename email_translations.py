WISHLIST_URL = "https://www.amazon.de/hz/wishlist/ls/214QLWQZ9B9DR?ref_=wl_share"

email_translations = {
    'en': {
        'subject_new': "You're on the list! 🎉 – Termin Notify",
        'subject_duplicate': "You're already subscribed – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hi {name},</p>
            <p>Thanks for signing up! You're now subscribed to notifications for <strong>{office}</strong> appointments in <strong>{city}</strong>. 📬<br>
            We'll ping you when something pops up!</p>
            <p>You can support us by checking out our <a href="{wishlist}">wishlist</a>. 🙌</p>
            <p>Changed your mind? You can <a href="{unsubscribe}">unsubscribe here</a>.</p>
            <p>Cheers,<br>Termin Checker Team</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hi {name},</p>
            <p>You're already on our list for <strong>{office}</strong> appointments in <strong>{city}</strong>. 📝<br>
            We'll keep an eye out and let you know when a spot opens!</p>
            <p>If you'd like to make our day, check out our <a href="{wishlist}">wishlist</a>. 🎁</p>
            <p>Want to unsubscribe? No hard feelings — just <a href="{unsubscribe}">click here</a>.</p>
            <p>Cheers,<br>Termin Checker Team</p>
        """
    },
    'fa': {
        'subject_new': "شما در لیست هستید! 🎉 – ترمین نوتیفای",
        'subject_duplicate': "شما قبلاً عضو شده‌اید – ترمین نوتیفای",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>{name} عزیز،</p>
            <p>ممنون که ثبت‌نام کردید! حالا شما در لیست اطلاع‌رسانی وقت‌های <strong>{office}</strong> در <strong>{city}</strong> هستید. 📬<br>
            به‌محض باز شدن وقت جدید بهتون خبر می‌دیم.</p>
            <p>می‌تونید از ما حمایت کنید با دیدن <a href="{wishlist}">لیست آرزوها</a> 🙌</p>
            <p>نظرتون عوض شده؟ <a href="{unsubscribe}">لغو عضویت</a> رو بزنید.</p>
            <p>با احترام،<br>تیم ترمین نوتیفای</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>{name} عزیز،</p>
            <p>شما قبلاً برای وقت <strong>{office}</strong> در <strong>{city}</strong> عضو شده‌اید. 📝<br>
            ما پیگیر هستیم و به‌محض باز شدن وقت بهتون اطلاع می‌دیم.</p>
            <p>اگه دوست داشتید خوشحالمون کنید، <a href="{wishlist}">لیست آرزوها</a> ما اینجاست. 🎁</p>
            <p>برای لغو عضویت، <a href="{unsubscribe}">اینجا کلیک کنید</a>.</p>
            <p>با احترام،<br>تیم ترمین نوتیفای</p>
        """
    },
    'de': {
        'subject_new': "Du stehst auf der Liste! 🎉 – Termin Notify",
        'subject_duplicate': "Du bist bereits abonniert – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hallo {name},</p>
            <p>Danke für deine Anmeldung! Du bekommst Benachrichtigungen für <strong>{office}</strong>-Termine in <strong>{city}</strong>. 📬<br>
            Wir informieren dich, sobald ein Termin frei wird!</p>
            <p>Unterstütze uns mit einem Blick auf unsere <a href="{wishlist}">Wunschliste</a>. 🙌</p>
            <p>Möchtest du dich abmelden? <a href="{unsubscribe}">Hier klicken</a>.</p>
            <p>Viele Grüße,<br>Termin Notify Team</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Hallo {name},</p>
            <p>Du bist bereits auf der Liste für <strong>{office}</strong>-Termine in <strong>{city}</strong>. 📝<br>
            Wir benachrichtigen dich, sobald ein Termin frei ist.</p>
            <p>Mach uns eine Freude und schau auf unsere <a href="{wishlist}">Wunschliste</a>. 🎁</p>
            <p>Abmelden? <a href="{unsubscribe}">Hier klicken</a>.</p>
            <p>Viele Grüße,<br>Termin Notify Team</p>
        """
    },
    'tr': {
        'subject_new': "Listeye eklendiniz! 🎉 – Termin Notify",
        'subject_duplicate': "Zaten abonesiniz – Termin Notify",
'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Merhaba {name},</p>
            <p>Kayıt olduğunuz için teşekkürler! Artık <strong>{city}</strong> şehrindeki <strong>{office}</strong> randevuları için bilgilendirileceksiniz. 📬</p>
            <p>Destek olmak isterseniz <a href="{wishlist}">dilek listemize</a> göz atabilirsiniz. 🙌</p>
            <p>Vazgeçtiniz mi? <a href="{unsubscribe}">Buradan ayrılabilirsiniz</a>.</p>
            <p>Sevgiler,<br>Termin Notify Ekibi</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Merhaba {name},</p>
            <p>Zaten <strong>{city}</strong> şehrindeki <strong>{office}</strong> randevuları için kayıtlısınız. 📝<br>
            Bir yer açıldığında sizi bilgilendireceğiz.</p>
            <p>İsterseniz <a href="{wishlist}">dilek listemize</a> göz atabilirsiniz. 🎁</p>
            <p>Aboneliği sonlandırmak için <a href="{unsubscribe}">buraya tıklayın</a>.</p>
            <p>Sevgiler,<br>Termin Notify Ekibi</p>
        """
    },
    'uk': {
        'subject_new': "Вас додано до списку! 🎉 – Termin Notify",
        'subject_duplicate': "Ви вже підписані – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Привіт {name},</p>
            <p>Дякуємо за підписку! Тепер ви отримуватимете сповіщення про <strong>{office}</strong> у <strong>{city}</strong>. 📬</p>
            <p>Підтримайте нас, переглянувши <a href="{wishlist}">наш список побажань</a>. 🙌</p>
            <p>Передумали? <a href="{unsubscribe}">Скасувати підписку</a>.</p>
            <p>З повагою,<br>Команда Termin Notify</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>Привіт {name},</p>
            <p>Ви вже підписані на сповіщення про <strong>{office}</strong> у <strong>{city}</strong>. 📝</p>
            <p>Ми повідомимо, коли з’явиться новий час.</p>
            <p><a href="{wishlist}">Список побажань</a> для підтримки. 🎁</p>
            <p><a href="{unsubscribe}">Відписатися</a></p>
            <p>З повагою,<br>Команда Termin Notify</p>
        """
    },
    'ar': {
        'subject_new': "تمت إضافتك للقائمة! 🎉 – Termin Notify",
        'subject_duplicate': "أنت مشترك بالفعل – Termin Notify",
        'body_new': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>مرحباً {name}،</p>
            <p>شكراً لتسجيلك! سيتم إعلامك بمواعيد <strong>{office}</strong> في <strong>{city}</strong>. 📬</p>
            <p>ادعمنا من خلال <a href="{wishlist}">قائمة الأمنيات</a>. 🙌</p>
            <p>هل غيّرت رأيك؟ <a href="{unsubscribe}">اضغط هنا لإلغاء الاشتراك</a>.</p>
            <p>مع تحياتنا،<br>فريق Termin Notify</p>
        """,
        'body_duplicate': lambda name, city, office, wishlist, unsubscribe: f"""
            <p>مرحباً {name}،</p>
            <p>أنت مشترك بالفعل في إشعارات <strong>{office}</strong> في <strong>{city}</strong>. 📝</p>
            <p>سنعلمك عند توفر موعد جديد.</p>
            <p><a href="{wishlist}">قائمة الأمنيات</a> إن أحببت أن تدعمنا. 🎁</p>
            <p><a href="{unsubscribe}">إلغاء الاشتراك</a></p>
            <p>مع تحياتنا،<br>فريق Termin Notify</p>
        """
    }
}
