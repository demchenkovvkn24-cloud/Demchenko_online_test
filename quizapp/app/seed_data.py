"""Демонстраційний тест для наповнення застосунку (без залежностей від Flask і БД)."""

DEMO_TITLE = "Основи веб-розробки"
DEMO_DESCRIPTION = "Демонстраційний тест: HTML, HTTP, архітектура та безпека веб-застосунків."

# (текст питання, бали, [(варіант, чи_правильна), ...])
DEMO_QUESTIONS = [
    ("Який HTML-тег створює гіперпосилання?", 1,
     [("<a>", True), ("<link>", False), ("<href>", False), ("<p>", False)]),
    ("Який HTTP-метод доцільно використовувати для надсилання форми входу з паролем?", 1,
     [("GET", False), ("POST", True), ("HEAD", False), ("OPTIONS", False)]),
    ("Що означає абревіатура CSS?", 1,
     [("Cascading Style Sheets", True), ("Computer Style System", False),
      ("Creative Site Scripts", False), ("Coded Server Syntax", False)]),
    ("Який код стану HTTP означає, що ресурс не знайдено?", 1,
     [("200", False), ("301", False), ("404", True), ("500", False)]),
    ("Яка вразливість полягає у впровадженні шкідливого скрипта на сторінку?", 2,
     [("SQL-ін'єкція", False), ("XSS", True), ("DDoS", False), ("Переповнення буфера", False)]),
    ("Що означає шаблон архітектури MVC?", 2,
     [("Model–View–Controller", True), ("Module–Version–Cache", False),
      ("Multi–Variable–Class", False), ("Main–View–Component", False)]),
    ("Які з наведених технологій використовують на серверній стороні?", 3,
     [("Flask", True), ("Django", True), ("Bootstrap", False), ("Node.js", True)]),
    ("Які заходи захищають від SQL-ін'єкцій?", 3,
     [("Параметризовані запити", True), ("Використання ORM", True),
      ("Конкатенація рядків у SQL-запиті", False), ("Валідація вхідних даних на сервері", True)]),
]
