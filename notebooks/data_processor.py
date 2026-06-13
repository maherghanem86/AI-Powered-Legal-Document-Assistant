import os
import re
import fitz  # مكتبة PyMuPDF للتعامل مع ملفات PDF
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
source_folder = os.path.join(script_dir, "raw_laws")
output_file = os.path.join(script_dir, "processed_laws.csv")

def clean_arabic_text(text):
    if not text:
        return ""
    
    # إزالة التشكيل والتطويل 
    text = re.sub(r'[\u0640]', '', text)
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\.{4,}', '', text)
    
    # توحيد الأحرف العربية (Arabic Normalization)
    text = re.sub(r'[إأآ]', 'ا', text) 
    text = re.sub(r'ى', 'ي', text)      
    text = re.sub(r'ة', 'ه', text)      
    
    # معالجة مشاكل الأسطر
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def process_legal_pdf(file_path, law_name):
    doc = fitz.open(file_path)
    full_text = []
    for page in doc:
        full_text.append(page.get_text())
        
    raw_text = '\n'.join(full_text)
    cleaned_text = clean_arabic_text(raw_text)
    
    # --- التعديل هنا: البحث عن "الماده" بالهاء لأن التاء المربوطة تم توحيدها ---
    pattern = r'(الماده\s*\d+|ماده\s*\d+\s*-?)'
    parts = re.split(pattern, cleaned_text)
    
    chunks = []
    
    if parts[0].strip():
        chunks.append({
            "law_name": law_name,
            "article": "مقدمه/تمهيد",
            "text": parts[0].strip(),
            "char_count": len(parts[0].strip())
        })
        
    for i in range(1, len(parts), 2):
        article_title = parts[i].strip()
        article_title = re.sub(r'[-:]', '', article_title).strip()
        
        article_content = parts[i+1].strip() if (i+1) < len(parts) else ""
        
        if article_content:
            full_article_text = f"{article_title}: {article_content}"
            chunks.append({
                "law_name": law_name,
                "article": article_title,
                "text": full_article_text,
                "char_count": len(full_article_text)
            })
            
    return chunks

def main():
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)
        print(f"تم إنشاء المجلد '{source_folder}'. يرجى وضع ملفات الـ PDF بداخله.")
        return

    print("بدء معالجة القوانين والتشريعات...")
    data_list = []
    
    for filename in os.listdir(source_folder):
        if filename.endswith(".pdf") and not filename.startswith("~"):
            file_path = os.path.join(source_folder, filename)
            law_name = filename.replace(".pdf", "").strip()
            
            try:
                law_chunks = process_legal_pdf(file_path, law_name)
                data_list.extend(law_chunks)
                print(f"تمت معالجة وتفكيك: {filename} (تم استخراج {len(law_chunks)} مقطع/مادة)")
            except Exception as e:
                print(f"حدث خطأ في الملف {filename}: {e}")

    if data_list:
        df = pd.DataFrame(data_list)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ تم الانتهاء! تم استخراج وحفظ إجمالي {len(data_list)} مادة/مقطع في الملف: {output_file}")
    else:
        print("لم يتم العثور على قوانين لمعالجتها.")

if __name__ == "__main__":
    main()