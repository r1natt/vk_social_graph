import argparse
import sys
import logging
from logger import setup_logger
from utils.reqs import VKAPIClient, VKAPIInterface
from db.db import CollectionFactory
from service.parser import VKParser
from service.gephi import GexfGraph
from models._types import VK_ID



setup_logger()

logger = logging.getLogger(__name__)


def parse_friends(vk_id: int, depth: int):
    logger.info("Запуск парсинга друзей для пользователя %s с глубиной %s", vk_id, depth)

    try:
        collection_factory = CollectionFactory()
        friends_collection = collection_factory.friend_collection()
        user_collection = collection_factory.user_collection()

        api_client = VKAPIClient()
        api_interface = VKAPIInterface(api_client)

        parser = VKParser(api_interface, friends_collection, user_collection)

        parser.search(vk_id, depth)

        logger.info("Парсинг завершен успешно")

    except Exception as e:
        logger.exception("Ошибка при парсинге: %s", e)
        sys.exit(1)

def build_graph(vk_id: int, depth: int):
    logger.info("Запуск построения графа для пользователя %s с глубиной %s", vk_id, depth)

    try:
        collection_factory = CollectionFactory()
        friends_collection = collection_factory.friend_collection()
        user_collection = collection_factory.user_collection()

        graph_builder = GexfGraph(friends_collection, user_collection)
        graph_builder.create(vk_id, depth, filename="first")

        logger.info("Граф успешно сформирован")
    except Exception as e:
        logger.exception("Ошибка при построении графа: %s", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Парсер друзей ВКонтакте',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py parse_friends 12345 2
  python main.py build_graph 12345 2
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    friends_parser = subparsers.add_parser(
        'parse_friends',
        help='Парсинг друзей пользователя ВКонтакте',
        description='Парсинг друзей пользователя ВКонтакте с заданной глубиной'
    )

    friends_parser.add_argument('vk_id', type=int, help='ID пользователя ВКонтакте')
    friends_parser.add_argument('depth', type=int, help='Глубина парсинга')
    friends_parser.add_argument('--vk_id', '-v', type=int, dest='vk_id_named')
    friends_parser.add_argument('--depth', '-d', type=int, dest='depth_named')

    graph_parser = subparsers.add_parser(
        'build_graph',
        help='Построение графа на основе данных о друзьях',
        description='Формирует граф друзей ВКонтакте с заданной глубиной'
    )

    graph_parser.add_argument('vk_id', type=int, help='ID пользователя ВКонтакте')
    graph_parser.add_argument('depth', type=int, help='Глубина построения графа (1-10)')
    graph_parser.add_argument('--vk_id', '-v', type=int, dest='vk_id_named')
    graph_parser.add_argument('--depth', '-d', type=int, dest='depth_named')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command in ['parse_friends', 'build_graph']:
        vk_id = args.vk_id_named if args.vk_id_named else args.vk_id
        depth = args.depth_named if args.depth_named else args.depth

        if not vk_id or not depth:
            subparser = friends_parser if args.command == 'parse_friends' else graph_parser
            subparser.error("Необходимо указать vk_id и depth")

        if vk_id <= 0:
            subparser.error("vk_id должен быть положительным числом")

        if depth <= 0 or depth > 10:
            subparser.error("depth должен быть 0 или больше")

        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        print(f"Команда: {args.command}")
        print(f"VK ID: {vk_id}")
        print(f"Глубина: {depth}")
        print("-" * 30)

        if args.command == 'parse_friends':
            parse_friends(vk_id, depth)
        elif args.command == 'build_graph':
            build_graph(vk_id, depth)


if __name__ == '__main__':
    main()
