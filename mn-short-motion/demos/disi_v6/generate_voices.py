#!/usr/bin/env python3
"""DISI V6: 9 real neural narrated language tracks, with word-level timestamps.
These are never represented as the approved Pelayo original.
"""
import asyncio, json, pathlib, sys
import edge_tts
ROOT=pathlib.Path("dubs");ROOT.mkdir(exist_ok=True)
data={
"en":{"voice":"en-GB-RyanNeural","text":"DTP evolves. DISI is born. Our roots are in human intelligence, known as HUMINT: human sources, field reporting and firsthand testimony. Journalism starts where events happen, not on a sofa. Yet influencers and YouTubers now present opinions about wars they have never witnessed or investigated as if those opinions were reporting. Passing unverified opinion off as journalism should almost be an offence. Millions of followers do not turn an opinion into a fact. We are building DISI to check news, verify photos and videos, identify manipulation, analyse metadata and geolocation, protect sources and preserve original evidence. One story, ten languages, international reach. We invite investors, sponsors and strategic partners to join the development of DISI."},
"fr":{"voice":"fr-FR-HenriNeural","text":"DTP évolue. DISI voit le jour. Notre origine est le renseignement humain, le HUMINT : les sources, le terrain et les témoignages directs. Le journalisme commence là où les événements se produisent, pas depuis un canapé. Pourtant, des influenceurs et des youtubeurs présentent aujourd'hui comme du journalisme leurs opinions sur des guerres qu'ils n'ont jamais vues ni étudiées. Faire passer des opinions non vérifiées pour de l'information devrait presque être un délit. Des millions d'abonnés ne transforment pas une opinion en fait. Nous construisons DISI pour vérifier les nouvelles, les photos, les vidéos, les métadonnées et la géolocalisation, détecter les manipulations, protéger les sources et conserver les originaux. Une information, dix langues, une portée internationale. Nous invitons investisseurs, mécènes et partenaires stratégiques à participer à son développement."},
"de":{"voice":"de-DE-ConradNeural","text":"DTP entwickelt sich weiter. DISI entsteht. Unser Ursprung ist HUMINT, die Arbeit mit menschlichen Quellen, Recherchen vor Ort und unmittelbaren Zeugenaussagen. Journalismus beginnt dort, wo die Ereignisse stattfinden, nicht auf dem Sofa. Trotzdem präsentieren Influencer und YouTuber Meinungen über Kriege, die sie nie selbst erlebt oder untersucht haben, als wären es journalistische Berichte. Ungeprüfte Meinungen als Journalismus auszugeben, sollte beinahe strafbar sein. Millionen Follower machen aus einer Meinung keine Tatsache. Wir entwickeln DISI, um Nachrichten, Fotos und Videos zu überprüfen, Manipulationen zu erkennen, Metadaten und Geolokalisierung zu analysieren und Quellen sowie Originaldateien zu schützen. Eine Nachricht, zehn Sprachen, internationale Reichweite. Wir laden Investoren, Sponsoren und strategische Partner ein, den Aufbau von DISI zu begleiten."},
"it":{"voice":"it-IT-DiegoNeural","text":"DTP si evolve. Nasce DISI. Le nostre origini sono nell'intelligence umana, HUMINT: le fonti, il lavoro sul campo e le testimonianze dirette. Il giornalismo nasce dove accadono i fatti, non su un divano. Eppure influencer e youtuber presentano come giornalismo opinioni su guerre che non hanno mai visto né indagato. Spacciare opinioni non verificate per informazione dovrebbe essere quasi un reato. Milioni di follower non trasformano un'opinione in un fatto. Stiamo costruendo DISI per verificare notizie, fotografie e video, individuare manipolazioni, analizzare metadati e geolocalizzazioni, proteggere le fonti e conservare i file originali. Una notizia, dieci lingue, portata internazionale. Invitiamo investitori, sponsor e partner strategici a partecipare allo sviluppo di DISI."},
"pt":{"voice":"pt-PT-DuarteNeural","text":"A DTP evolui. Nasce a DISI. A nossa origem está na inteligência humana, HUMINT: fontes, investigação no terreno e testemunhos diretos. O jornalismo começa onde os acontecimentos ocorrem, não num sofá. No entanto, influenciadores e youtubers apresentam como jornalismo opiniões sobre guerras que nunca testemunharam nem investigaram. Fazer passar opiniões não verificadas por informação deveria ser quase um crime. Milhões de seguidores não transformam uma opinião num facto. Estamos a construir a DISI para verificar notícias, fotografias e vídeos, detetar manipulações, analisar metadados e geolocalizações, proteger as fontes e preservar os ficheiros originais. Uma notícia, dez línguas, alcance internacional. Convidamos investidores, patrocinadores e parceiros estratégicos a participar no desenvolvimento da DISI."},
"ru":{"voice":"ru-RU-DmitryNeural","text":"ДТП развивается. Рождается ДИСИ. Наша основа — агентурная информация, человеческие источники, работа на месте событий и непосредственные свидетельства. Журналистика начинается там, где происходят события, а не на диване. Однако инфлюенсеры и ютуберы выдают за журналистику мнения о войнах, которых они никогда не видели и не изучали. Выдавать непроверенные мнения за проверенную информацию почти должно считаться правонарушением. Миллионы подписчиков не превращают мнение в факт. Мы создаём ДИСИ, чтобы проверять новости, фотографии и видео, выявлять манипуляции, анализировать метаданные и геолокацию, защищать источники и сохранять оригиналы файлов. Одна новость, десять языков, международный охват. Мы приглашаем инвесторов, спонсоров и стратегических партнёров участвовать в развитии ДИСИ."},
"zh":{"voice":"zh-CN-YunxiNeural","text":"DTP正在发展，DISI由此诞生。我们的根基是人力情报，也就是HUMINT：来自现场的消息来源、调查和第一手证词。新闻报道应该从事件发生的地方开始，而不是坐在沙发上发表评论。然而，一些网红和视频博主把自己从未亲历、也从未调查过的战争评论包装成新闻。把未经核实的观点当作新闻，几乎应该被视为违法。数百万粉丝并不能把观点变成事实。我们正在建设DISI，用于核查新闻、照片和视频，识别篡改，分析元数据和地理位置，保护消息来源并保存原始文件。一条新闻，十种语言，面向国际受众。我们邀请投资者、赞助者和战略合作伙伴共同参与DISI的发展。"},
"ja":{"voice":"ja-JP-KeitaNeural","text":"DTPは進化し、DISIが誕生します。私たちの出発点はヒューミント、つまり人間の情報源、現場での調査、そして直接得られた証言です。報道は出来事の現場から始まるものであり、ソファに座って作るものではありません。それにもかかわらず、現地を訪れたことも調査したこともない戦争について、インフルエンサーやユーチューバーが意見を報道として発信しています。検証されていない意見をニュースとして扱うことは、ほとんど違法と言えるほど深刻です。何百万人ものフォロワーがいても、意見が事実になるわけではありません。私たちはニュースや写真、動画を検証し、改ざんを発見し、メタデータや位置情報を分析し、情報源と原本を守るDISIを構築しています。一つのニュース、十の言語、世界への発信。投資家、スポンサー、戦略的パートナーの皆様をDISIの開発にお招きします。"},
"ar":{"voice":"ar-SA-HamedNeural","text":"تتطور دي تي بي، وتولد ديسي. تنطلق جذورنا من الاستخبارات البشرية، أي المصادر الإنسانية والعمل الميداني والشهادات المباشرة. تبدأ الصحافة من المكان الذي تقع فيه الأحداث، لا من الأريكة. ومع ذلك، يقدم المؤثرون وصناع الفيديو آراءهم حول حروب لم يشهدوها ولم يحققوا فيها، وكأنها تقارير صحفية. إن تقديم آراء غير موثقة على أنها أخبار يستحق أن يعد فعلاً مخالفاً. ملايين المتابعين لا تحول الرأي إلى حقيقة. نبني ديسي للتحقق من الأخبار والصور ومقاطع الفيديو، وكشف التلاعب، وتحليل البيانات الوصفية والمواقع الجغرافية، وحماية المصادر والاحتفاظ بالملفات الأصلية. خبر واحد، عشر لغات، وصول دولي. ندعو المستثمرين والرعاة والشركاء الاستراتيجيين للمشاركة في تطوير ديسي."}
}
async def generate(language,entry):
    output=ROOT/f"DISI_{language}.mp3"
    moments=[]
    for attempt in range(4):
        try:
            chunks=[]
            comm=edge_tts.Communicate(entry["text"],entry["voice"],rate="-3%")
            async for x in comm.stream():
                if x["type"]=="audio": chunks.append(x["data"])
                elif x["type"]=="WordBoundary":
                    moments.append({"text":x["text"],"offset":x["offset"],"duration":x["duration"]})
            sound=b"".join(chunks)
            if len(sound)<20000: raise RuntimeError("empty neural voice")
            output.write_bytes(sound)
            (ROOT/f"DISI_{language}_words.json").write_text(json.dumps(moments,ensure_ascii=False))
            print(f"OK {language} bytes={len(sound)} words={len(moments)}",flush=True)
            return
        except Exception as e:
            print(f"RETRY {language} #{attempt+1}: {e}",flush=True)
            moments.clear()
            if attempt==3: raise
            await asyncio.sleep(4+attempt*7)
async def main():
    for lang, entry in data.items():await generate(lang,entry)
    (ROOT/"translations.json").write_text(json.dumps(data,ensure_ascii=False,indent=2))
asyncio.run(main())
