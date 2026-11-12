# فيديوهات الهيرو

حط الفيديو بهالمجلد بالاسم المطلوب وبيظهر لحاله بالهيرو (تشغيل تلقائي صامت + زر "اضغط لتشغيل الصوت").
بدون فيديو، الهيرو بيضل بدونه.

| الصفحة              | الفيديو                       | الغلاف (اختياري)                   |
|---------------------|-------------------------------|------------------------------------|
| الرئيسية `/`         | home_hero.mp4 (أو .webm)      | home_hero_poster.jpg (أو .webp)    |
| `/english-ielts`     | english_hero.mp4              | english_hero_poster.jpg            |
| `/private-tutoring`  | tutoring_hero.mp4             | tutoring_hero_poster.jpg           |
| `/women-courses`     | women_hero.mp4                | women_hero_poster.jpg              |
| `/saudi-online`      | saudi_hero.mp4                | saudi_hero_poster.jpg              |

بديل للملف: System Parameter برابط الفيديو (إله الأولوية):
  alomran.<home|english|tutoring|women|saudi>_hero_video_url
  alomran.<...>_hero_poster_url

ضغط الفيديو:
  ffmpeg -i input.mp4 -vf "scale='min(1920,iw)':-2,fps=30" -c:v libx264 -preset slow -crf 26 \
         -profile:v high -pix_fmt yuv420p -c:a aac -b:a 128k -ac 2 -movflags +faststart saudi_hero.mp4
  ffmpeg -i saudi_hero.mp4 -ss 00:00:01 -frames:v 1 -q:v 3 saudi_hero_poster.jpg
