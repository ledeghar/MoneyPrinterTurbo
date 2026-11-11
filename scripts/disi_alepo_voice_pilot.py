#!/usr/bin/env python3
"""Narration-only pilot for ALEPO, 10 real Edge TTS voices.
No social upload, no licensed imagery and no paid API keys.
Input text is a critical recommendation grounded in the supplied author manuscript.
"""
import asyncio
import json
from pathlib import Path
import edge_tts

DATA = {
    "es": ("es-MX-PelayoNeural", """Hay libros que te llevan al frente. Y otros que te obligan a mirar a quienes quedaron atrás. Alepo: Los cristianos olvidados, de Juan Manuel Ledesma, reconstruye una operación de evacuación en Siria, en 2014, a partir de hechos relatados por su autor. La prosa es directa, visual y de ritmo tenso: informes de inteligencia, calles destruidas y decisiones tomadas en segundos. Su mayor acierto es recordar que detrás de la acción hay familias que necesitan salir. Una lectura recomendable para quienes buscan crónica bélica, memoria y dilemas humanos. Ya a la venta en Amazon. ¿Leerás el libro o esperarás la película?"""),
    "en": ("en-GB-RyanNeural", """Some books take you to the front line. Others make you look at those left behind. Aleppo: The Forgotten Christians, by Juan Manuel Ledesma, recounts an evacuation operation in Syria in 2014, based on events described by its author. The prose is direct, visual and tense: intelligence reports, shattered streets and decisions made in seconds. Its greatest strength is reminding us that behind the action are families who need to escape. Recommended for readers interested in war reporting, memory and human dilemmas. Available now on Amazon. Will you read the book, or wait for the film?"""),
    "fr": ("fr-FR-HenriNeural", """Certains livres nous emmènent au front. D'autres nous obligent à regarder ceux qui sont restés. Alep, les chrétiens oubliés, de Juan Manuel Ledesma, raconte une évacuation en Syrie en 2014, à partir de faits rapportés par l'auteur. L'écriture est directe, visuelle et tendue : rapports de renseignement, rues détruites et décisions prises en quelques secondes. Sa principale force est de rappeler que derrière l'action, des familles cherchent à survivre. Une lecture recommandée aux amateurs de récits de guerre et de mémoire humaine. Disponible sur Amazon. Lirez-vous le livre ou attendrez-vous le film ?"""),
    "de": ("de-DE-ConradNeural", """Manche Bücher führen uns an die Front. Andere zeigen uns die Menschen, die zurückbleiben. Aleppo, die vergessenen Christen, von Juan Manuel Ledesma erzählt von einer Evakuierung in Syrien im Jahr 2014, anhand von Ereignissen, die der Autor schildert. Der Stil ist direkt, bildhaft und spannend: Geheimdienstberichte, zerstörte Straßen und Entscheidungen in Sekunden. Seine größte Stärke liegt darin, an die Familien hinter den Kampfhandlungen zu erinnern. Empfehlenswert für Leser von Kriegsreportagen und menschlichen Schicksalen. Jetzt bei Amazon erhältlich. Liest du das Buch oder wartest du auf den Film?"""),
    "it": ("it-IT-DiegoNeural", """Alcuni libri ci portano al fronte. Altri ci costringono a guardare chi è rimasto indietro. Aleppo, i cristiani dimenticati, di Juan Manuel Ledesma, racconta un'evacuazione in Siria nel 2014, basandosi sui fatti narrati dall'autore. La prosa è diretta, visiva e tesa: rapporti d'intelligence, strade distrutte e decisioni prese in pochi secondi. Il suo pregio maggiore è ricordare che dietro l'azione ci sono famiglie da salvare. Lettura consigliata a chi cerca memoria, cronaca di guerra e dilemmi umani. Disponibile su Amazon. Leggerai il libro o aspetterai il film?"""),
    "pt": ("pt-PT-DuarteNeural", """Há livros que nos levam à frente de batalha. Outros obrigam-nos a olhar para quem ficou para trás. Alepo, os cristãos esquecidos, de Juan Manuel Ledesma, relata uma evacuação na Síria em 2014, com base nos acontecimentos narrados pelo autor. A escrita é direta, visual e intensa: relatórios de inteligência, ruas destruídas e decisões tomadas em segundos. A sua maior força é lembrar que, por trás da ação, há famílias que precisam de sair. Leitura recomendada para quem procura reportagem de guerra e memória humana. Já disponível na Amazon. Vais ler o livro ou esperar pelo filme?"""),
    "ru": ("ru-RU-DmitryNeural", """Одни книги переносят нас на передовую. Другие заставляют увидеть тех, кто остался позади. Алеппо: забытые христиане Хуана Мануэля Ледесмы рассказывает об эвакуации в Сирии в 2014 году, опираясь на события, описанные автором. Стиль прямой, яркий и напряжённый: разведывательные сводки, разрушенные улицы и решения за считаные секунды. Главная сила книги в напоминании о семьях, которым необходимо спастись. Рекомендуем всем, кто интересуется военной хроникой и человеческими судьбами. Книга доступна на Amazon. Вы прочтёте её или дождётесь фильма?"""),
    "zh": ("zh-CN-YunxiNeural", """有些书带我们走上前线，有些书让我们看见被遗忘的人。胡安·曼努埃尔·莱德斯马的《阿勒颇：被遗忘的基督徒》，根据作者讲述的事件，重现了2014年叙利亚的一次撤离行动。文字直接、生动、紧张：情报报告、被摧毁的街道、转瞬之间的决定。它最大的力量，是提醒我们，在战斗背后，有等待撤离的家庭。推荐给关注战争纪实、记忆和人性抉择的读者。本书现已在亚马逊发售。你会读这本书，还是等待电影？"""),
    "ja": ("ja-JP-KeitaNeural", """前線へ連れていく本もあれば、取り残された人々に目を向けさせる本もあります。フアン・マヌエル・レデスマ著『アレッポ、忘れられたキリスト教徒』は、著者が語る事実をもとに、2014年のシリアでの避難作戦を描きます。情報報告、破壊された街、瞬時の決断。文章は率直で、映像的で、緊張感に満ちています。この作品の魅力は、戦いの陰で助けを待つ家族を忘れないことです。戦争の記録と人間の選択に関心のある方におすすめです。アマゾンで発売中。本を読みますか、それとも映画を待ちますか。"""),
    "ar": ("ar-SA-HamedNeural", """بعض الكتب تأخذنا إلى خطوط المواجهة، وأخرى تجعلنا نرى من تُركوا خلفها. يروي كتاب حلب، المسيحيون المنسيون، للكاتب خوان مانويل ليديسما، عملية إجلاء في سوريا عام ألفين وأربعة عشر، استناداً إلى أحداث يرويها المؤلف. الكتابة مباشرة وبصرية ومتوترة: تقارير استخبارات، وشوارع مدمرة، وقرارات تُتخذ في ثوانٍ. تكمن قوته في تذكيرنا بأن خلف القتال عائلات تبحث عن النجاة. قراءة ننصح بها لمحبي شهادات الحرب والذاكرة الإنسانية. الكتاب متاح الآن على أمازون. هل ستقرأ الكتاب أم تنتظر الفيلم؟"""),
}

async def go():
    out = Path("alepo-tts-output")
    out.mkdir(exist_ok=True)
    results = {}
    errors = {}
    for code, (voice, text) in DATA.items():
        path = out / f"ALEPO_{code}.mp3"
        options = [voice]
        if code == "es":
            options.append("es-ES-AlvaroNeural")
        elif code == "ru":
            options.extend(["ru-RU-SvetlanaNeural", "ru-RU-DariyaNeural"])
        for candidate in options:
            print("TRY", code, candidate, flush=True)
            try:
                await edge_tts.Communicate(text=text, voice=candidate, rate="+8%").save(str(path))
                if path.stat().st_size < 1000:
                    raise RuntimeError("Empty TTS")
                results[code] = {"voice":candidate, "text":text,
                                 "file":path.name, "bytes":path.stat().st_size,
                                 "pelayo_requested": code == "es",
                                 "pelayo_delivered": candidate == "es-MX-PelayoNeural"}
                break
            except Exception as exc:
                errors[f"{code}:{candidate}"] = str(exc)
                if path.exists():
                    path.unlink()
        if code not in results:
            print("UNAVAILABLE", code, flush=True)
    (out/"manifest.json").write_text(json.dumps(
        {"completed":results,"failed_attempts":errors,
         "complete_ten_tracks":len(results)==10,
         "pelayo_original":results.get("es",{}).get("pelayo_delivered",False)},
        ensure_ascii=False,indent=2),encoding="utf8")
    print("VOICE_GENERATION_COMPLETED:", len(results), "of 10", flush=True)
    if len(results) < 1:
        raise RuntimeError("TTS service unavailable")

if __name__=="__main__":
    asyncio.run(go())
