import re

class PIIScrubber:
    """
    Layer 1: Input Sandboxing [cite: 1006]
    """
    EMAIL_REGEX = r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b'
    PHONE_REGEX = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    SSN_REGEX = r'\b\d{3}-\d{2}-\d{4}\b'

    @classmethod
    def scrub(cls, text: str) -> str:
        """
        Redact sensitive information from text.
        """
        scrubbed_text = re.sub(cls.EMAIL_REGEX, '[EMAIL]', text)
        scrubbed_text = re.sub(cls.PHONE_REGEX, '[PHONE]', scrubbed_text)
        scrubbed_text = re.sub(cls.SSN_REGEX, '[SSN]', scrubbed_text)
        return scrubbed_text
