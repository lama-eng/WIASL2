# backend/services/ai_service.py
import re
import logging
from datetime import datetime
import numpy as np
from transformers import pipeline
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    """AI Service with real ML models for case analysis"""
    
    def __init__(self, use_gpu=False):
        logger.info("Initializing AI Service with ML models...")
        
        # تحديد الجهاز (CPU/GPU)
        self.device = 0 if use_gpu and torch.cuda.is_available() else -1
        
        # تحميل النماذج
        self.load_models()
        
        # الاحتفاظ ببعض القواعد كـ fallback
        self.init_knowledge_base()
        
        logger.info("AI Service initialized successfully")
    
    def load_models(self):
        """Load ML models for analysis"""
        try:
            logger.info("Loading ML models...")
            
            # 1. نموذج التصنيف بدون تدريب (Zero-shot)
            self.classifier = pipeline(
                "zero-shot-classification",
                model="joeddav/xlm-roberta-large-xnli",
                device=self.device
            )
            
            # 2. نموذج تحليل المشاعر (للاستعجال)
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=self.device
            )
            
            # 3. نموذج التعرف على الكيانات الطبية (اختياري)
            try:
                self.medical_ner = pipeline(
                    "ner",
                    model="samrawal/bert-base-uncased_clinical-ner",
                    device=self.device,
                    aggregation_strategy="simple"
                )
            except:
                logger.warning("Medical NER model not available, using fallback")
                self.medical_ner = None
            
            # 4. نموذج الترجمة (للواجهة العربية)
            self.translator = pipeline(
                "translation",
                model="Helsinki-NLP/opus-mt-ar-en",
                device=self.device
            ) 
            
            logger.info("ML models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            logger.warning("Using rule-based fallback only")
            self.classifier = getattr(self, 'classifier', None)
            self.sentiment_analyzer = getattr(self, 'sentiment_analyzer', None)
            self.medical_ner = getattr(self, 'medical_ner', None)
            self.translator = getattr(self, 'translator', None)
    
    def init_knowledge_base(self):
        """Initialize knowledge base for rule-based fallback"""
        
        # نفس الكود القديم للقواعد - للاستخدام عند فشل الـ AI
        self.urgency_keywords = {
            'critical': {
                'words': ['emergency', 'critical', 'life-threatening', 'dying', 'immediate', 
                         'death', 'save life', 'cpr', 'rescue', 'intensive care', 'icu',
                         'طوارئ', 'حرج', 'يموت', 'موت', 'إنقاذ', 'عناية مركزة', 'خطير جدا', 'فوري'],
                'weight': 0.3
            },
            'high': {
                'words': ['urgent', 'serious', 'severe', 'danger', 'risk', 'quickly', 'asap',
                         'desperate', 'crisis', 'acute', 'worsening',
                         'عاجل', 'خطير', 'شديد', 'خطر', 'أزمة', 'يتدهور', 'ضروري', 'ملح'],
                'weight': 0.2
            },
            'medium': {
                'words': ['soon', 'need', 'required', 'necessary', 'important', 'help',
                         'assistance', 'support', 'struggling',
                         'محتاج', 'ضروري', 'مهم', 'مساعدة', 'دعم', 'معاناة', 'صعب'],
                'weight': 0.1
            },
            'low': {
                'words': ['would like', 'interested', 'maybe', 'perhaps', 'considering',
                         'eventually', 'sometime',
                         'أرغب', 'ربما', 'ممكن', 'لاحقا'],
                'weight': 0.05
            }
        }
        
        # Medical keywords (fallback)
        self.medical_keywords = {
            'conditions': [
                'cancer', 'tumor', 'leukemia', 'heart disease', 'stroke', 'diabetes',
                'kidney failure', 'liver disease', 'pneumonia', 'infection', 'sepsis',
                'covid', 'coronavirus', 'cerebral palsy', 'autism', 'paralysis',
                'سرطان', 'ورم', 'سكري', 'قلب', 'كلى', 'كبد', 'شلل', 'صرع',
                'التهاب', 'عدوى', 'ضغط', 'أنيميا', 'ربو', 'توحد'
            ],
            'treatments': [
                'surgery', 'operation', 'transplant', 'chemotherapy', 'radiation',
                'dialysis', 'mri', 'ct scan', 'x-ray', 'physical therapy',
                'عملية', 'جراحة', 'زراعة', 'كيماوي', 'غسيل كلى',
                'أشعة', 'علاج طبيعي', 'دواء'
            ],
            'symptoms': [
                'pain', 'fever', 'bleeding', 'difficulty breathing', 'shortness of breath',
                'unconscious', 'seizure', 'vomiting', 'severe headache', 'chest pain',
                'ألم', 'حمى', 'نزيف', 'ضيق تنفس', 'إغماء',
                'تشنج', 'صداع', 'قيء', 'ألم صدر'
            ]
        }
        
        # Children indicators (fallback)
        self.children_keywords = {
            'direct': [
                'child', 'children', 'kid', 'kids', 'baby', 'babies', 'infant',
                'toddler', 'son', 'daughter', 'grandchild',
                'طفل', 'أطفال', 'رضيع', 'ابن', 'ابنة', 'بنت', 'أولاد', 'بنات', 'صغير'
            ]
        }

        self.non_essential_keywords = [
            'trip', 'travel', 'vacation', 'holiday', 'beach', 'sea', 'tourism',
            'picnic', 'resort', 'relax', 'relaxation', 'rest', 'entertainment',
            'رحلة', 'سفر', 'إجازة', 'البحر', 'شاطئ', 'استجمام', 'ترفيه', 'فسحة',
            'منتجع', 'نزهة', 'راحة نفسية'
        ]

        self.asset_purchase_keywords = [
            'buy a car', 'buy car', 'purchase a car', 'vehicle', 'car', 'automobile',
            'buy a house', 'buy house', 'villa', 'luxury home', 'property purchase',
            'اشتري عربية', 'شراء عربية', 'اشتري عربيه', 'شراء عربيه', 'سيارة', 'عربية', 'عربيه',
            'سياره',
            'فيلا', 'بيت فاخر', 'مكان فاخر', 'شراء منزل'
        ]

        self.luxury_keywords = [
            'luxury', 'luxurious', 'fancy', 'premium', 'high-end', 'villa', 'resort',
            'فاخر', 'فخمة', 'مكان فاخر', 'فيلا', 'رفاهية'
        ]

        self.work_necessity_keywords = [
            'for work', 'to go to work', 'commute', 'job commute', 'work transportation',
            'عشان اروح الشغل', 'عشان اروح العمل', 'للذهاب إلى العمل', 'للشغل', 'للعمل'
        ]

        self.essential_medical_keywords = [
            'medicine', 'medication', 'treatment', 'prescription', 'chronic', 'chronic disease',
            'daily medication', 'hospital', 'clinic', 'doctor', 'operation', 'surgery',
            'دواء', 'أدوية', 'علاج', 'وصفة', 'مرض مزمن', 'مزمن', 'علاج يومي',
            'مستشفى', 'عيادة', 'طبيب', 'عملية', 'جراحة'
        ]
        
        # Categories for zero-shot classification
        self.categories = ['medical', 'rent', 'education', 'food', 'utilities', 'clothing', 'other']

        # Category keywords for rule-based fallback
        self.category_keywords = {
            'medical': [
                'doctor', 'hospital', 'medicine', 'treatment', 'surgery', 'health', 'clinic',
                'diagnosis', 'prescription', 'therapy', 'medical', 'sick', 'disease', 'illness',
                'طبيب', 'مستشفى', 'دواء', 'علاج', 'عملية', 'صحة', 'مرض', 'عيادة', 'تشخيص'
            ],
            'rent': [
                'rent', 'house', 'apartment', 'eviction', 'landlord', 'housing', 'shelter', 'homeless',
                'إيجار', 'بيت', 'شقة', 'سكن', 'إخلاء', 'مأوى', 'مشرد', 'منزل'
            ],
            'education': [
                'school', 'university', 'tuition', 'education', 'student', 'college', 'book', 'study',
                'مدرسة', 'جامعة', 'رسوم', 'تعليم', 'طالب', 'كلية', 'دراسة', 'كتب'
            ],
            'food': [
                'food', 'hungry', 'meal', 'groceries', 'nutrition', 'feed', 'starving',
                'طعام', 'جوع', 'وجبة', 'غذاء', 'تغذية', 'إطعام', 'جائع'
            ],
            'utilities': [
                'electricity', 'water', 'gas', 'bill', 'utility', 'power', 'internet',
                'كهرباء', 'ماء', 'غاز', 'فاتورة', 'خدمات', 'إنترنت'
            ],
            'clothing': [
                'clothes', 'clothing', 'shoes', 'uniform', 'winter', 'blanket', 'coat',
                'ملابس', 'أحذية', 'زي', 'بطانية', 'شتاء', 'معطف'
            ],
            'other': [
                'other', 'help', 'support', 'need', 'assistance',
                'مساعدة', 'دعم', 'احتياج', 'عون'
            ]
        }
    
    def analyze_case_comprehensive(self, case_data):
        """
        Main method to analyze a help case using AI models
        """
        try:
            text = case_data.get('description', '')
            metadata = {
                'income': float(case_data.get('income', 0)),
                'family_size': int(case_data.get('family_size', 1)),
                'children_count': int(case_data.get('children_count', 0))
            }
            
            logger.info(f"Analyzing case with AI: {text[:100]}...")
            
            # ترجمة النص لو كان عربي (اختياري)
            text_en = self._translate_if_arabic(text)
            
            # تحليل متوازي باستخدام AI والنماذج
            results = {}
            
            context_flags = self._extract_context_flags(text)

            # 1. تصنيف النص (Category)
            if self.classifier:
                category_result = self._ai_detect_category(text_en, text_original=text, context_flags=context_flags)
            else:
                category_result = self._detect_category(text)
            
            # 2. تحليل الاستعجال (Urgency) - hybrid: keywords + sentiment
            if self.sentiment_analyzer:
                urgency_result = self._ai_detect_urgency(text_en, text_original=text)
            else:
                urgency_result = self._detect_urgency(text)
            
            # 3. تحليل المخاطر الطبية
            medical_result = self._ai_detect_medical_risk(text_en, text_original=text, context_flags=context_flags)
            
            # 4. كشف الأطفال (استخدم الـ AI أو القواعد)
            children_result = self._detect_children(text)  # القواعد كويسة هنا
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(
                urgency_result['score'],
                medical_result['score'],
                children_result['score'],
                metadata,
                category_result=category_result,
                context_flags=context_flags
            )
            
            # Build human-readable explanation
            reasons = []
            if urgency_result['level'] in ('critical', 'high'):
                reasons.append(f"urgency level: {urgency_result['level']}")
            if medical_result['level'] == 'high':
                reasons.append('serious medical condition detected')
            if context_flags.get('luxury_purchase'):
                reasons.append('luxury purchase request detected')
            elif context_flags.get('asset_purchase'):
                reasons.append('asset purchase request detected')
            if context_flags.get('non_essential'):
                reasons.append('non-essential / leisure request detected')
            if children_result['present']:
                count_str = f" ({children_result['count']})" if children_result.get('count') else ''
                reasons.append(f"children present{count_str}")
            income = metadata.get('income', 0)
            if income < 500:
                reasons.append('very low income')
            elif income < 1000:
                reasons.append('limited income')
            if metadata.get('family_size', 1) > 4:
                reasons.append(f"large family ({metadata['family_size']} members)")
            reasons.extend((urgency_result.get('factors', []) + medical_result.get('factors', []))[:3])
            
            # Prepare comprehensive result
            result = {
                'urgency': {
                    'score': urgency_result['score'],
                    'level': urgency_result['level'],
                    'factors': urgency_result.get('factors', []),
                    'sentiment': urgency_result.get('sentiment', {})
                },
                'medical_risk': {
                    'score': medical_result['score'],
                    'level': medical_result['level'],
                    'factors': medical_result.get('factors', []),
                    'entities': medical_result.get('entities', [])
                },
                'children': {
                    'present': children_result['present'],
                    'score': children_result['score'],
                    'count': children_result.get('count'),
                    'factors': children_result.get('factors', [])
                },
                'category': {
                    'category': category_result['category'],
                    'confidence': category_result['confidence'],
                    'all_scores': category_result.get('all_scores', {})
                },
                'priority_score': priority_score,
                'confidence_scores': {
                    'overall': 0.95 if self.classifier else 0.85,
                    'urgency': urgency_result.get('confidence', 0.8),
                    'medical': medical_result.get('confidence', 0.8),
                    'children': children_result.get('confidence', 0.8),
                    'category': category_result['confidence']
                },
                'explanation': reasons,
                'model_used': 'ai' if self.classifier else 'rule-based',
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"AI Analysis complete: Priority={priority_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_case: {e}")
            return self._get_default_analysis()
    
    def _ai_detect_category(self, text, text_original=None, context_flags=None):
        """Detect category using zero-shot classification"""
        try:
            context_flags = context_flags or {}
            original_text = text_original or text

            if context_flags.get('non_essential'):
                return {
                    'category': 'other',
                    'confidence': 0.95,
                    'all_scores': {'other': 0.95},
                    'factors': ['non-essential request detected']
                }

            # Zero-shot classification
            result = self.classifier(
                text,
                candidate_labels=self.categories,
                hypothesis_template="This text is about {}."
            )
            
            # Get best category
            best_idx = result['scores'].index(max(result['scores']))
            best_category = result['labels'][best_idx]
            confidence = result['scores'][best_idx]
            
            # Create scores dict
            scores = {label: score for label, score in zip(result['labels'], result['scores'])}
            
            rule_result = self._detect_category(original_text)
            rule_scores = rule_result.get('scores', {})
            rule_top_score = max(rule_scores.values()) if rule_scores else 0

            if rule_top_score >= 2 and rule_result['category'] != best_category:
                return {
                    'category': rule_result['category'],
                    'confidence': max(rule_result['confidence'], min(confidence + 0.1, 0.95)),
                    'all_scores': scores,
                    'factors': [f"rule override: {rule_result['category']}"]
                }

            return {
                'category': best_category,
                'confidence': confidence,
                'all_scores': scores,
                'factors': [f"AI confidence: {confidence:.2f}"]
            }
            
        except Exception as e:
            logger.error(f"Error in AI category detection: {e}")
            return self._detect_category(text_original or text)
    
    def _ai_detect_urgency(self, text_en, text_original=None):
        """Hybrid urgency detection: keyword signals + sentiment analysis"""
        try:
            # 1. Keyword-based score on original text (handles Arabic directly)
            keyword_result = self._detect_urgency(text_original or text_en)
            keyword_score = keyword_result['score']
            
            # 2. Sentiment-based score on translated/English text
            sentiment_score = 0.4  # neutral default
            sentiment = None
            try:
                sentiment = self.sentiment_analyzer(text_en)[0]
                label = sentiment['label'].lower()
                conf = sentiment['score']
                if label == 'negative':
                    # Negative sentiment raises urgency, but not as much as explicit keywords
                    sentiment_score = 0.4 + (conf * 0.35)
                elif label == 'positive':
                    sentiment_score = max(0.05, 0.4 - (conf * 0.2))
                else:
                    sentiment_score = 0.35
            except Exception as se:
                logger.warning(f"Sentiment analysis failed: {se}")
            
            # 3. Hybrid: keywords 60%, sentiment 40%
            # Keywords are more reliable for medical/urgent context
            score = (keyword_score * 0.6) + (sentiment_score * 0.4)

            original_text = (text_original or text_en).lower()
            if any(term in original_text for term in ['عملية عاجلة', 'جراحة عاجلة', 'عملية جراحية عاجلة', 'urgent surgery', 'emergency operation']):
                score += 0.25
            if any(term in original_text for term in ['مرض مزمن', 'دواء يومي', 'daily medication', 'chronic disease']):
                score += 0.12
            if self._is_non_essential_request(original_text) or self._is_asset_purchase_request(original_text):
                score -= 0.25

            score = min(max(score, 0), 1.0)
            
            if score >= 0.7:
                level = 'critical'
            elif score >= 0.5:
                level = 'high'
            elif score >= 0.3:
                level = 'medium'
            else:
                level = 'low'
            
            factors = list(keyword_result.get('factors', []))
            if sentiment:
                factors.append(f"Sentiment: {sentiment['label']} ({sentiment['score']:.2f})")
            
            return {
                'score': score,
                'level': level,
                'sentiment': sentiment or {},
                'confidence': min(0.6 + score * 0.35, 0.95),
                'factors': list(set(factors))[:6]
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid urgency detection: {e}")
            return self._detect_urgency(text_original or text_en)
    
    def _ai_detect_medical_risk(self, text, text_original=None, context_flags=None):
        """Detect medical risk using critical terms, NER, and keywords"""
        try:
            context_flags = context_flags or {}
            score = 0
            factors = []
            entities = []
            original_text = text_original or text
            combined_text = f"{text} {original_text}".lower()

            if context_flags.get('non_essential') and not context_flags.get('essential_medical'):
                return {
                    'score': 0,
                    'level': 'low',
                    'factors': ['non-medical leisure request'],
                    'entities': [],
                    'confidence': 0.9
                }
            
            # Critical medical terms — high weight boost (checked first on original text)
            critical_medical_terms = [
                'surgery', 'operation', 'transplant', 'chemotherapy', 'dialysis',
                'intensive care', 'icu', 'life support', 'cancer', 'tumor', 'leukemia',
                'heart failure', 'kidney failure', 'stroke', 'cerebral palsy',
                'عملية', 'جراحة', 'عملية جراحية', 'عملية عاجلة', 'جراحة عاجلة',
                'كيماوي', 'غسيل كلى', 'عناية مركزة', 'سرطان', 'ورم', 'فشل كلوي',
                'فشل قلبي', 'شلل دماغي', 'مرض مزمن', 'دواء يومي', 'أدوية بشكل يومي'
            ]
            text_lower_init = combined_text
            for term in critical_medical_terms:
                if term in text_lower_init:
                    score += 0.25
                    factors.append(f"Critical: '{term}'")
            
            # Use medical NER if available
            if self.medical_ner:
                ner_results = self.medical_ner(text)
                
                medical_entities = [
                    ent for ent in ner_results 
                    if any(term in ent['entity_group'].lower() 
                          for term in ['disease', 'symptom', 'treatment', 'medication'])
                ]
                
                for entity in medical_entities:
                    score += 0.15
                    entities.append({
                        'text': entity['word'],
                        'type': entity['entity_group'],
                        'score': entity['score']
                    })
                    factors.append(f"Medical entity: {entity['word']} ({entity['entity_group']})")
            
            # Also check medical keywords as fallback
            text_lower = combined_text
            for term in self.medical_keywords['conditions']:
                if term in text_lower:
                    score += 0.2
                    factors.append(f"Condition: '{term}'")
            
            for term in self.medical_keywords['treatments']:
                if term in text_lower:
                    score += 0.18
                    factors.append(f"Treatment: '{term}'")

            for term in self.medical_keywords['symptoms']:
                if term in text_lower:
                    score += 0.15
                    factors.append(f"Symptom: '{term}'")
            
            # Normalize
            score = min(score, 1.0)
            
            # Determine level
            if score >= 0.6:
                level = 'high'
            elif score >= 0.3:
                level = 'medium'
            else:
                level = 'low'
            
            return {
                'score': score,
                'level': level,
                'factors': list(set(factors))[:5],
                'entities': entities[:5],
                'confidence': min(0.5 + score * 0.5, 0.95)
            }
            
        except Exception as e:
            logger.error(f"Error in AI medical detection: {e}")
            return self._detect_medical_risk(text)
    def _translate_if_arabic(self, text):
        """Translate Arabic text to English (optional)"""
        if any('\u0600' <= c <= '\u06FF' for c in text):
            if hasattr(self, 'translator') and self.translator:
                try:
                    result = self.translator(text, max_length=512)
                    return result[0]['translation_text']
                except Exception as e:
                    logger.warning(f"Translation failed: {e}")
                    return text
        return text
    
    def _detect_urgency(self, text):
        """Detect urgency level in text"""
        text_lower = text.lower()
        score = 0
        factors = []
        matched_keywords = []
        
        # Check for urgency keywords
        for level, data in self.urgency_keywords.items():
            for keyword in data['words']:
                if keyword in text_lower:
                    score += data['weight']
                    matched_keywords.append(keyword)
                    factors.append(f"{level}: '{keyword}'")
        
        # Check for exclamation marks (indicates high urgency)
        exclamation_count = text.count('!')
        if exclamation_count > 0:
            exclamation_score = min(0.1 * exclamation_count, 0.3)
            score += exclamation_score
            factors.append(f"exclamation marks: {exclamation_count}")
        
        # Check for ALL CAPS words (shouting/emphasis)
        words = text.split()
        caps_count = sum(1 for word in words if word.isupper() and len(word) > 2)
        if caps_count > 0:
            caps_score = min(0.1 * caps_count, 0.2)
            score += caps_score
            factors.append(f"ALL CAPS words: {caps_count}")
        
        # Check for urgent time references
        time_patterns = [
            r'immediate', r'right now', r'as soon as possible', r'today',
            r'tonight', r'within \d+ (hours|days)', r'by tomorrow',
            r'اليوم', r'فور[اًا]', r'خلال \d+ (?:ساعة|ساعات|يوم|أيام)', r'غد[اًا]?'
        ]
        for pattern in time_patterns:
            if re.search(pattern, text_lower):
                score += 0.15
                factors.append(f"time urgency: {pattern}")

        if any(term in text_lower for term in ['عملية عاجلة', 'جراحة عاجلة', 'عملية جراحية عاجلة', 'urgent surgery', 'emergency operation']):
            score += 0.35
            factors.append('critical procedure request')

        if any(term in text_lower for term in ['مرض مزمن', 'دواء يومي', 'daily medication', 'chronic disease']):
            score += 0.15
            factors.append('ongoing essential treatment')

        if self._is_non_essential_request(text_lower) or self._is_asset_purchase_request(text_lower):
            score = max(0, score - 0.3)
            factors.append('non-essential purchase/leisure request')
        
        # Normalize score to 0-1
        score = min(score, 1.0)
        
        # Determine urgency level
        if score >= 0.7:
            level = 'critical'
        elif score >= 0.5:
            level = 'high'
        elif score >= 0.3:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'score': score,
            'level': level,
            'factors': list(set(factors))[:5],  # Remove duplicates, limit to 5
            'confidence': min(0.5 + score * 0.5, 0.95)
        }
    
    def _detect_medical_risk(self, text):
        """Detect medical risk in text"""
        text_lower = text.lower()
        score = 0
        factors = []
        medical_terms_found = []

        if self._is_non_essential_request(text_lower) and not any(term in text_lower for term in self.essential_medical_keywords):
            return {
                'score': 0,
                'level': 'low',
                'factors': ['non-medical leisure request'],
                'terms_found': [],
                'confidence': 0.9
            }

        critical_medical_terms = [
            'surgery', 'operation', 'urgent surgery', 'emergency operation', 'transplant',
            'chemotherapy', 'dialysis', 'cancer', 'tumor', 'leukemia', 'heart failure',
            'kidney failure', 'stroke', 'chronic disease', 'daily medication',
            'عملية', 'جراحة', 'عملية جراحية', 'عملية جراحية عاجلة', 'عملية عاجلة',
            'كيماوي', 'غسيل كلى', 'سرطان', 'ورم', 'فشل كلوي', 'مرض مزمن',
            'أدوية بشكل يومي', 'دواء يومي'
        ]

        for term in critical_medical_terms:
            if term in text_lower:
                score += 0.22
                medical_terms_found.append(term)
                factors.append(f"critical medical term: '{term}'")
        
        # Check all medical categories
        for category, terms in self.medical_keywords.items():
            for term in terms:
                if term in text_lower:
                    term_score = 0.15
                    if category == 'conditions':
                        term_score = 0.2
                    elif category == 'symptoms':
                        term_score = 0.15
                    elif category == 'treatments':
                        term_score = 0.12
                    elif category == 'facilities':
                        term_score = 0.1
                    
                    score += term_score
                    medical_terms_found.append(term)
                    factors.append(f"{category}: '{term}'")

        if any(term in text_lower for term in ['مرض مزمن', 'chronic disease', 'أدوية بشكل يومي', 'daily medication']):
            score += 0.18
            factors.append('essential ongoing treatment')
        
        # Check for medical urgency indicators
        medical_urgency = ['emergency', 'critical', 'life-threatening', 'severe', 'urgent', 'عاجل', 'خطير']
        for word in medical_urgency:
            if word in text_lower:
                score += 0.2
                factors.append(f"medical urgency: '{word}'")
        
        # Normalize score
        score = min(score, 1.0)
        
        # Determine risk level
        if score >= 0.6:
            level = 'high'
        elif score >= 0.3:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'score': score,
            'level': level,
            'factors': list(set(factors))[:5],
            'terms_found': list(set(medical_terms_found))[:5],
            'confidence': min(0.5 + score * 0.5, 0.95)
        }
    
    def _detect_children(self, text):
        """Detect presence of children in text"""
        text_lower = text.lower()
        score = 0
        factors = []
        children_terms = []
        
        # Check direct children keywords
        for category, terms in self.children_keywords.items():
            for term in terms:
                if term in text_lower:
                    if category == 'direct':
                        score += 0.25
                    elif category == 'age_specific':
                        score += 0.2
                    elif category == 'context':
                        score += 0.15
                    
                    children_terms.append(term)
                    factors.append(f"{category}: '{term}'")
        
        # Extract number of children if mentioned
        children_count = None
        count_patterns = [
            r'(\d+)\s*(?:children|kids|sons|daughters)',
            r'(?:children|kids):\s*(\d+)',
            r'(\d+)\s*(?:child|kid)'
        ]
        
        for pattern in count_patterns:
            match = re.search(pattern, text_lower)
            if match:
                children_count = int(match.group(1))
                factors.append(f"explicit count: {children_count}")
                break
        
        # Normalize score
        score = min(score, 1.0)
        
        return {
            'present': score > 0.2,
            'score': score,
            'count': children_count,
            'factors': list(set(factors))[:5],
            'terms_found': list(set(children_terms))[:5],
            'confidence': min(0.5 + score * 0.5, 0.95)
        }
    
    def _detect_category(self, text):
        """Detect case category"""
        text_lower = text.lower()

        if self._is_non_essential_request(text_lower) or self._is_asset_purchase_request(text_lower):
            return {
                'category': 'other',
                'confidence': 0.95,
                'scores': {'other': 3},
                'matched_keywords': ['non-essential request']
            }

        category_scores = {}
        category_factors = {}
        
        # Calculate score for each category
        for category, keywords in self.category_keywords.items():
            score = 0
            matched = []
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched.append(keyword)
            category_scores[category] = score
            category_factors[category] = matched[:3]
        
        # Find best category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[best_category]

            if max_score == 0:
                return {
                    'category': 'other',
                    'confidence': 0.5,
                    'scores': category_scores,
                    'matched_keywords': []
                }
            
            # Calculate confidence based on score and text length
            text_length = len(text.split())
            confidence = min(max_score / max(5, text_length * 0.1), 0.95)
            
            return {
                'category': best_category,
                'confidence': max(confidence, 0.5),
                'scores': category_scores,
                'matched_keywords': category_factors[best_category]
            }
        
        return {
            'category': 'other',
            'confidence': 0.5,
            'scores': {},
            'matched_keywords': []
        }
    
    def _calculate_priority_score(self, urgency_score, medical_score, children_score, metadata, category_result=None, context_flags=None):
        """Calculate final priority score (0-100)"""
        category_result = category_result or {}
        context_flags = context_flags or {}
        
        # Base score from text analysis
        base_priority = (
            urgency_score * 40 +      # 40% weight
            medical_score * 30 +       # 30% weight
            children_score * 20        # 20% weight
        )
        
        # Critical medical boost: serious medical cases deserve significantly higher priority
        if medical_score >= 0.6:
            base_priority += 15
        elif medical_score >= 0.4:
            base_priority += 8
        
        # Socioeconomic factors (40% of total)
        socioeconomic_score = 0
        
        # Income factor (lower income = higher priority)
        income = metadata.get('income', 0)
        if income < 500:
            socioeconomic_score += 20
        elif income < 1000:
            socioeconomic_score += 15
        elif income < 2000:
            socioeconomic_score += 10
        elif income < 3000:
            socioeconomic_score += 5
        
        # Family size factor (larger family = higher priority)
        family_size = metadata.get('family_size', 1)
        if family_size > 6:
            socioeconomic_score += 15
        elif family_size > 4:
            socioeconomic_score += 10
        elif family_size > 2:
            socioeconomic_score += 5
        
        # Children count factor (more children = higher priority)
        children_count = metadata.get('children_count', 0)
        if children_count > 3:
            socioeconomic_score += 15
        elif children_count > 1:
            socioeconomic_score += 10
        elif children_count > 0:
            socioeconomic_score += 5
        
        # Combine base priority and socioeconomic factors
        # Base priority contributes 60%, socioeconomic contributes 40%
        final_priority = (base_priority * 0.6) + (socioeconomic_score * 0.4)

        if context_flags.get('essential_medical'):
            final_priority += 10

        if medical_score >= 0.6 and urgency_score >= 0.5:
            final_priority += 10

        if context_flags.get('non_essential'):
            final_priority = min(final_priority, 12)

        if context_flags.get('asset_purchase'):
            final_priority = min(final_priority, 18 if context_flags.get('work_related_transport') else 10)

        if context_flags.get('luxury_purchase'):
            final_priority = min(final_priority, 6)

        if category_result.get('category') == 'medical' and final_priority < 35 and not context_flags.get('asset_purchase') and not context_flags.get('luxury_purchase'):
            final_priority = max(final_priority, 35)
        
        # Ensure priority is between 0 and 100
        final_priority = max(0, min(100, final_priority))
        
        # Round to 1 decimal place
        return round(final_priority, 1)
    
    def _get_default_analysis(self):
        """Return default analysis when something goes wrong"""
        return {
            'urgency': {
                'score': 0.5,
                'level': 'medium',
                'factors': ['default analysis']
            },
            'medical_risk': {
                'score': 0.3,
                'level': 'medium',
                'factors': ['default analysis']
            },
            'children': {
                'present': False,
                'score': 0,
                'factors': ['default analysis']
            },
            'category': {
                'category': 'other',
                'confidence': 0.5
            },
            'priority_score': 50.0,
            'confidence_scores': {
                'overall': 0.5,
                'urgency': 0.5,
                'medical': 0.5,
                'children': 0.5,
                'category': 0.5
            },
            'analyzed_at': datetime.utcnow().isoformat()
        }

    def _is_non_essential_request(self, text):
        text_lower = text.lower()
        return any(term in text_lower for term in self.non_essential_keywords)

    def _is_asset_purchase_request(self, text):
        text_lower = text.lower()
        return any(term in text_lower for term in self.asset_purchase_keywords)

    def _is_luxury_request(self, text):
        text_lower = text.lower()
        return any(term in text_lower for term in self.luxury_keywords)

    def _extract_context_flags(self, text):
        text_lower = text.lower()
        non_essential = self._is_non_essential_request(text_lower)
        asset_purchase = self._is_asset_purchase_request(text_lower)
        luxury_purchase = self._is_luxury_request(text_lower)
        essential_medical = any(term in text_lower for term in self.essential_medical_keywords)
        work_related_transport = any(term in text_lower for term in self.work_necessity_keywords)
        return {
            'non_essential': non_essential,
            'essential_medical': essential_medical,
            'asset_purchase': asset_purchase,
            'luxury_purchase': luxury_purchase,
            'work_related_transport': work_related_transport
        }


# Create a singleton instance
ai_service = AIService()