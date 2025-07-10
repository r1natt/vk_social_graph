class TPSBucket:
    """
    TPS - transaction per second
    VK API имеют лимиты на запросы (5 запросов в секунду, но позволяют они немного 
    больше). Все дело в том, что пока я выполняю запросы к api без прокси и в 
    одном процессе, поэтому мне нужно, чтобы запросы проходили в одной очереди с 
    минимальными задержками, пока не достигнут лимит запросов в секунду

    TPSBucket - решает эту проблему, по сути своей это отдельный процесс, который 
    следит за достижением лимита, и каждую секунду обновляет количество запросов 
    на заданное число

    Важно отметить, что этот класс будет работать и с запросами, поступающеми от 
    разных процессов одновременно
    """
    def __init__(self, expected_tps):
        self.number_of_tokens = Value('i', 0)
        self.expected_tps = expected_tps
        self.bucket_refresh_process = Process(target=self.refill_bucket_per_second)

    def refill_bucket_per_second(self):
        time.sleep(1 - (time.time() % 1))
        while True:
            self.refill_bucket()
            # print(datetime.datetime.now().strftime('%H:%M:%S.%f'), "refill")
            time.sleep(1)

    def refill_bucket(self):
        self.number_of_tokens.value = self.expected_tps

    def start(self):
        self.bucket_refresh_process.start()

    def stop(self):
        self.bucket_refresh_process.kill()

    def get_token(self):
        response = False
        if self.number_of_tokens.value > 0:
            with self.number_of_tokens.get_lock():
                if self.number_of_tokens.value > 0:
                    self.number_of_tokens.value -= 1
                    response = True
        return response


def bucket_queue(func):
    """
    Проверяет достигнут ли лимит запросов в эту секунду, если он достигнут, цикл while будет ждать следующей секунды, чтобы выполнить заданную функцию
    """
    def exec_or_wait(*args, **kwargs):
        while True:
            if tps_bucket.get_token():
                query = func(*args, **kwargs)
                return query
    return exec_or_wait