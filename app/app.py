
from flask import Flask, render_template, request
from PyPDF2 import PdfReader
import io
from spacy.matcher import Matcher
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

app = Flask(__name__)

nlp = spacy.load('en_core_web_lg')
skill_path = './datasets/skills.jsonl'
ruler = nlp.add_pipe("entity_ruler")
ruler.from_disk(skill_path)

matcher = Matcher(nlp.vocab)
matcher.add("EMAIL", [[{"LIKE_EMAIL": True}]], greedy="LONGEST")
matcher.add("URL", [[{"LIKE_URL": True}]], greedy="LONGEST")


# clean the text
def preprocessing(sen):
    stopwords = list(STOP_WORDS)
    doc = nlp(sen)
    clean_sen = [token.lemma_.lower().strip() for token in doc if
                 token.text not in stopwords and token.is_punct == False and token.pos_ != "SYM" and token.pos_ != "SPACE"]
    return " ".join(clean_sen)


# extract text from pdf
def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += preprocessing(pdf_reader.pages[page_num].extract_text())
    return text


# Extract entities
def get_entities(text):
    doc = nlp(text)
    matches = matcher(doc)
    features = {
        "PERSON": [],
        "SKILL": [],
        "ORG": [],
        "GPE": [],
        "EMAIL": [],
        "URL": []
    }
    for ent in doc.ents:
        if ent.label_ in features:
            features[ent.label_].append(ent.text)
            features[ent.label_] = list(set(features[ent.label_]))

    for match_id, start, end in matches:
        string_id = nlp.vocab.strings[match_id]
        span = doc[start:end]
        if string_id in features:
            features[string_id].append(span.text)
            features[string_id] = list(set(features[string_id]))

    # make values join
    for key, value in features.items():
        features[key] = ", ".join(value)

    return features


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('file[]')
        extracted_texts = []
        for file in files:
            if file.filename != '':
                extracted_text = extract_text_from_pdf(file)
                result = get_entities(extracted_text)
                extracted_texts.append(result)
        print(extracted_texts)
        return render_template('index.html', extracted_texts=extracted_texts)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")

