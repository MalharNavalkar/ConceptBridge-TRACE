LESSON = {
    "slug": "half-adder",
    "title": "Half Adder — Digital Logic Design",
    "language_review": "Hindi and Hinglish wording is a draft for demonstration; please have a fluent technical educator review it before classroom use.",
    "modes": {
        "en": {
            "label": "English", "intro": "A half adder is a combinational logic circuit that adds two one-bit binary inputs. It produces a Sum bit and a Carry bit.",
            "inputs": "A and B are each either 0 or 1. Add their values as ordinary binary digits.",
            "outputs": "Sum is A XOR B: it is 1 when the inputs differ. Carry is A AND B: it is 1 only when both inputs are 1.",
            "gates": "The XOR gate computes Sum; the AND gate computes Carry. A half adder has no carry-in input.",
            "examples": ["0 + 0 = 00₂ → Sum 0, Carry 0", "0 + 1 = 01₂ → Sum 1, Carry 0", "1 + 0 = 01₂ → Sum 1, Carry 0", "1 + 1 = 10₂ → Sum 0, Carry 1"],
        },
        "hi": {
            "label": "हिन्दी", "intro": "हाफ ऐडर एक combinational logic circuit है जो दो एक-bit binary inputs को जोड़ता है। इसके outputs Sum bit और Carry bit होते हैं।",
            "inputs": "A और B, दोनों की value 0 या 1 होती है। इन्हें binary digits की तरह जोड़ें।",
            "outputs": "Sum = A XOR B: inputs अलग हों तो Sum 1 होता है। Carry = A AND B: Carry केवल तब 1 होता है जब दोनों inputs 1 हों।",
            "gates": "XOR gate Sum निकालता है और AND gate Carry निकालता है। Half adder में carry-in input नहीं होता।",
            "examples": ["0 + 0 = 00₂ → Sum 0, Carry 0", "0 + 1 = 01₂ → Sum 1, Carry 0", "1 + 0 = 01₂ → Sum 1, Carry 0", "1 + 1 = 10₂ → Sum 0, Carry 1"],
        },
        "hinglish": {
            "label": "Hinglish", "intro": "Half Adder ek combinational logic circuit hai jo do one-bit binary inputs ko add karta hai. Iske outputs Sum bit aur Carry bit hote hain.",
            "inputs": "A aur B dono ki value 0 ya 1 hoti hai. Inhe binary digits ki tarah add karo.",
            "outputs": "Sum = A XOR B: jab inputs different hon, Sum 1 hota hai. Carry = A AND B: sirf dono inputs 1 hone par Carry 1 hota hai.",
            "gates": "XOR gate Sum calculate karta hai aur AND gate Carry calculate karta hai. Half Adder mein carry-in input nahi hota.",
            "examples": ["0 + 0 = 00₂ → Sum 0, Carry 0", "0 + 1 = 01₂ → Sum 1, Carry 0", "1 + 0 = 01₂ → Sum 1, Carry 0", "1 + 1 = 10₂ → Sum 0, Carry 1"],
        },
    },
    "truth_table": [
        {"a": 0, "b": 0, "sum": 0, "carry": 0},
        {"a": 0, "b": 1, "sum": 1, "carry": 0},
        {"a": 1, "b": 0, "sum": 1, "carry": 0},
        {"a": 1, "b": 1, "sum": 0, "carry": 1},
    ],
}
