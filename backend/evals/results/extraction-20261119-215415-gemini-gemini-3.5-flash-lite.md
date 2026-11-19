# Teklif çıkarma değerlendirmesi — gemini:gemini-3.5-flash-lite

- Tarih: 2026-11-19T21:54:15+00:00  ·  Veri seti: `evals/extraction/dataset.jsonl` (30 belge)
- Prompt: `quote-extract-v1`

| Ölçüt | Değer | Hedef |
|---|---|---|
| 4. Alan doğruluğu | %99.3 (762 alan) | ✅ ≥ %90 |
| 5. İşaretsiz geçen yanlış tutar | 0 | ✅ 0 |
| Tutar doğruluğu | %100.0 | |
| Yanlış tutar / doğrulamanın yakaladığı | 0 / 0 | |
| Doğru ama işaretlenmiş alan (yanlış alarm) | 31 | |
| Teklif mi değil mi doğruluğu | %100.0 | |
| Model hatası (çıktı alınamadı) | 0 | |
| Ortanca süre (belge başına) | 1.564 sn | |

## Tuzaklı belgeler

- ✓ **ex-005** (para birimi yazılmamış) 
- ✓ **ex-010** (teslim süresi hafta olarak) 
- ✓ **ex-015** (tedarikçi satır tutarını yanlış yazmış) 
- ✓ **ex-020** (teklif değil, irsaliye) 
- ✓ **ex-023** (miktarsız fiyat teklifi) 
- ✓ **ex-027** (genel toplam tutmuyor) 

## Hatalı alanlar (⚑ = doğrulama işaretledi)

- **ex-016** (xlsx_totals): lines[0].lead_time_days: None (beklenen 21), lines[1].lead_time_days: None (beklenen 7), lines[2].lead_time_days: None (beklenen 7), lines[3].lead_time_days: None (beklenen 7), lines[4].lead_time_days: None (beklenen 10)
