import sys
import os
from dotenv import load_dotenv

# Добавляем папку src в sys.path, чтобы импорты работали
sys.path.insert(0, os.path.dirname(__file__))

# Загружаем .env из корня проекта (родительская папка)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from embedding_service import EmbeddingService
from pinecone_service import PineconeService
from data_loader import DataLoader
from searcher import Searcher

# 1. Инициализация сервисов (внедрение зависимостей)
embedding_service = EmbeddingService()
pinecone_service = PineconeService()

# 2. Подключение к индексу (индекс должен быть создан заранее)
pinecone_service.connect_to_index()

# 3. Загрузка данных (50 фраз)
phrases = [
    "Nissan Juke – компактный кроссовер с необычным дизайном.",
    "Volkswagen Beetle – символ эпохи хиппи и один из самых узнаваемых автомобилей.",
    "Nissan Juke оснащается турбированным двигателем 1.6 литра.",
    "Volkswagen Beetle имеет заднемоторную компоновку в классических версиях.",
    "Nissan Juke получил систему полного привода ALL-MODE 4x4.",
    "Volkswagen Beetle был разработан Фердинандом Порше в 1930-х годах.",
    "Nissan Juke предлагает спортивный режим движения с усиленной реакцией на газ.",
    "Volkswagen Beetle в 1960-х годах стал культовым автомобилем в США.",
    "Nissan Juke имеет систему кругового обзора Around View Monitor.",
    "Volkswagen Beetle отличается округлыми формами и хромированными деталями.",
    "Nissan Juke оснащается автоматической коробкой передач CVT.",
    "Volkswagen Beetle имеет багажник спереди и двигатель сзади.",
    "Nissan Juke обладает клиренсом 180 мм, подходящим для лёгкого бездорожья.",
    "Volkswagen Beetle выпускался в версии кабриолет с мягким верхом.",
    "Nissan Juke имеет светодиодные фары и дневные ходовые огни.",
    "Volkswagen Beetle был популярен благодаря своей надёжности и простоте.",
    "Nissan Juke оснащается мультимедийной системой с 7-дюймовым экраном.",
    "Volkswagen Beetle участвовал в гонках и ралли, но чаще использовался как городской автомобиль.",
    "Nissan Juke имеет спортивные сиденья с усиленной боковой поддержкой.",
    "Volkswagen Beetle часто называют 'Жук' или 'Фольксваген Жук'.",
    "Nissan Juke предлагает систему дистанционного запуска двигателя.",
    "Volkswagen Beetle в 1998 году получил новое поколение с более современным дизайном.",
    "Nissan Juke имеет вместительный багажник для своего класса.",
    "Volkswagen Beetle был героем многих фильмов и мультфильмов (например, 'Герби').",
    "Nissan Juke оснащается системой контроля тяги и стабилизации.",
    "Volkswagen Beetle имеет характерный звук двигателя, который ценят энтузиасты.",
    "Nissan Juke доступен в ярких цветах кузова, включая оранжевый и синий.",
    "Volkswagen Beetle стал одним из самых продаваемых автомобилей в истории.",
    "Nissan Juke имеет функцию помощи при старте на подъёме.",
    "Volkswagen Beetle часто используется для тюнинга и кастомизации.",
    "Nissan Juke оснащается системой бесключевого доступа и запуска.",
    "Volkswagen Beetle в 2003 году завершил производство в Мексике.",
    "Nissan Juke предлагает пакет Nismo с улучшенной подвеской и внешностью.",
    "Volkswagen Beetle был назван 'Car of the Century' в 1999 году? (нет, но очень популярен).",
    "Nissan Juke имеет два варианта двигателя: бензиновый и дизельный (в некоторых рынках).",
    "Volkswagen Beetle имеет характерный для своего времени интерьер с большим спидометром.",
    "Nissan Juke оснащается системой экстренного торможения в городе.",
    "Volkswagen Beetle был известен своей экономичностью и неприхотливостью.",
    "Nissan Juke имеет спортивный руль с кнопками управления аудио.",
    "Volkswagen Beetle выпускался в версии '1200', '1300', '1500' в зависимости от объёма двигателя.",
    "Nissan Juke получил награду за дизайн в 2011 году.",
    "Volkswagen Beetle имеет малый радиус разворота, удобный в городе.",
    "Nissan Juke оснащается системой адаптивного круиз-контроля.",
    "Volkswagen Beetle стал символом немецкого экономического чуда.",
    "Nissan Juke имеет три режима движения: Normal, Sport, Eco.",
    "Volkswagen Beetle в 2019 году был снят с производства окончательно.",
    "Nissan Juke предлагает панорамную крышу с электроприводом.",
    "Volkswagen Beetle имеет уникальный дизайн передней части с круглыми фарами.",
    "Nissan Juke оснащается системой помощи при парковке.",
    "Volkswagen Beetle – это не просто автомобиль, а культурный феномен."
]

data_loader = DataLoader(embedding_service, pinecone_service)
data_loader.load_phrases(phrases, category="auto", start_id=1)

# 4. Поиск по смыслу (5 запросов)
searcher = Searcher(embedding_service, pinecone_service)

queries = [
    "Какой автомобиль стал символом эпохи хиппи?",
    "Какая марка предлагает систему кругового обзора?",
    "У какого автомобиля заднемоторная компоновка?",
    "Какие авто имеют турбированный двигатель?",
    "Что общего между Nissan Juke и Volkswagen Beetle?"
]

for query in queries:
    print(f"\n=== Запрос: '{query}' ===")
    results = searcher.search(query, top_k=5)
    searcher.print_results(results)

print("\nДомашнее задание выполнено успешно!")