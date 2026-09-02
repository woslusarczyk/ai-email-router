import logging
from dataclasses import dataclass, field

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

from app.config import MODEL_NAME, OLLAMA_HOST
from app.departments import Department
from app.mailer import send_email as send_email_smtp

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

SYSTEM_PROMPT = """
Jesteś zaawansowanym systemem kategoryzującym zgłoszenia wewnątrz firmowe. Twoim jedynym zadaniem jest analiza 
wiadomości od użytkownika, przypisanie jej do odpowiedniego działu i przekazanie dalej za pomocą narzędzia 'send_email'.

KATEGORIE DO WYBORU:
- human-resources: sprawy ogólne w firmie, rekrutacja, rozwój pracowników, sprawy administracyjno-prawne.
- help-desk: rozwiązywanie problemów ze sprzętem, kontem użytkownika, aplikacjami użytkownika, problem z hasłami, 
pocztą lub awarie.
- it: programowanie aplikacji, stron internetowych, utrzymanie serwerów, baz danych, sieci, ochrona danych firmowych.
- kadry: sprawy związane z umowami pracowników, świadectw pracy, zaświadczeń, ewidencja czasu pracy, zwolnienia, 
zatrudnienia, podwyżki, płace, urlopy, zwolnienia lekarskie, ubezpieczenia społeczne.
- other: pozostałe sprawy, które nie kwalifikują się do żadnej z powyższych kategorii.

INSTRUKCJA:
1. Przeanalizuj dokładnie treść zgłoszenia podaną przez użytkownika.
2. Dopasuj zgłoszenie do jednej (i tylko jednej) z powyższych kategorii. Zwróć uwagę na subtelne różnice 
(np. 'kadry' to twarde dokumenty i płace, a 'human-resources' to miękki HR i rozwój).
3. Wygeneruj krótki, zwięzły temat (subject) zgłoszenia (np. "Brak dostępu do poczty", "Wniosek urlopowy").
4. Wywołaj narzędzie 'send_email' DOKŁADNIE JEDEN RAZ.
5. Nie dodawaj żadnego tekstu pobocznego, wyjaśnień ani przywitań.
"""

model = OllamaModel(MODEL_NAME, provider=OllamaProvider(base_url=f"{OLLAMA_HOST}/v1"))


@dataclass
class Deps:
    sender_email: str
    message: str
    resolved_department: Department | None = field(default=None, init=False)


agent = Agent(model, deps_type=Deps, system_prompt=SYSTEM_PROMPT)


@agent.tool
async def send_email(ctx: RunContext[Deps], department: Department, subject: str) -> str:
    """Send the original, verbatim report by email to the given department, replying to the original sender."""
    send_email_smtp(
        to=department.email,
        reply_to=ctx.deps.sender_email,
        subject=subject,
        body=ctx.deps.message,
    )
    ctx.deps.resolved_department = department
    return f"Wyslano zgloszenie do dzialu {department.value}."


def route_message(sender_email: str, message: str) -> Department:
    deps = Deps(sender_email=sender_email, message=message)
    prompt = message

    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = agent.run_sync(prompt, deps=deps)

        if deps.resolved_department is not None:
            return deps.resolved_department

        logger.warning(
            "Attempt %d/%d: agent did not call send_email, got plain text instead: %r",
            attempt,
            MAX_ATTEMPTS,
            result.output,
        )
        prompt = (
            "Nie wywolales narzedzia send_email. Musisz wywolac je teraz, dokladnie raz, "
            f"dla ponizszego zgloszenia:\n\n{message}"
        )

    logger.error("Agent failed to call send_email after %d attempts, falling back to OTHER", MAX_ATTEMPTS)
    send_email_smtp(
        to=Department.OTHER.email,
        reply_to=sender_email,
        subject="Nieskategoryzowane zgloszenie",
        body=message,
    )
    return Department.OTHER
