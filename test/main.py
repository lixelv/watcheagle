from time import sleep

while True:
    with open("test/1.txt", encoding="utf-8") as file:
        print(file.read())
    sleep(1)
