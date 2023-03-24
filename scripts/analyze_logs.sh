trans_array=("alibaba" "baidu" "bing" "caiyun" "deepl" "google" "iciba" "iflytek" "itranslate" "lingvanex"
           "niutrans" "papago" "reverso" "sogou" "tencent" "translateCom" "yandex" "youdao")

echo 'Succeeded\tToo Many Requests\tForbidden\tNonetype\tOther\tTranslator'
for i in "${trans_array[@]}"
do
  success=$(grep 'completed' logs/*.translation.log | sort -u | rev | cut -d: -f2 | rev | cut -d ' ' -f 7 | sort | grep $i | wc -l)
  too_many_requests=$(grep '429\|max retries\aborted' logs/*.translation.log | grep $i |  sort -u | wc -l)
  forbidden=$(grep '403' logs/*.translation.log | grep $i |  sort -u | wc -l)
  none_type=$(grep 'NoneType' logs/*.translation.log | grep $i | grep 429 |  sort -u | wc -l)
  other_errors=$(grep "out of range\|'data'\|477" logs/*.translation.log | grep $i | grep 429 |  sort -u | wc -l)
  echo  "$success\t$too_many_requests\t$forbidden\t$none_type\t$other_errors\t$i"

done