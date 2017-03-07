#coding:utf-8

from spider import *
import sys

def query_search(SpiderHandle, SID, query_input, editions, startYear, endYear):
    '''
        SpiderHandle: Spider instance
        SID: the session ID
        query_input: query set
        editions: indexs. eg. SCI/SSCI/AHCI
        startYear: start year
        endYear: end year
        (records_num): return the num of records for query.
    '''
    base_url = 'http://apps.webofknowledge.com/'
    query_url = 'summary.do?product=WOS&parentProduct=WOS&search_mode=AdvancedSearch&qid=1&SID='
    query_acts = '&page=1&action=changePageSize&pageSize=50'
    datas = {
        'product': 'WOS', 
        'search_mode': 'AdvancedSearch',
        'SID': SID,
        'action': 'search',
        'goToPageLoc': 'SearchHistoryTableBanner',
        'value(input1)': query_input,
        'value(searchOp)': 'search', 
        'x': '85', 
        'y': '442',
        'value(select2)': 'LA', 
        'value(select3)': 'DT', 
        'value(limitCount)':14,
        'limitStatus': 'expanded',
        'ss_lemmatization': 'On',
        'ss_spellchecking': 'Suggest',
        'period':'Year Range',
        'startYear': startYear,
        'endYear': endYear,
        'range': 'ALL',  
        'editions': editions,
        'update_back2search_link_param':'yes',
        'rs_sort_by': 'PY.A;LD.A;SO.A;VL.A;PG.A;AU.A'  #oldest-newest
        #'rs_sort_by': 'PY.D;LD.D;SO.A;VL.D;PG.A;AU.A' #newest-oldest
    }
    res = requests.post("http://apps.webofknowledge.com/WOS_AdvancedSearch.do", data=datas)
    html = res.text.encode('utf-8')
    records_num = re.findall('<a href="/summary.do?(.*?)" title="Click to view the results">(.*?)</a>', html)[0][1]
    print records_num
    f = open('search_result.html','w')
    f.write(html)
    f.close()
    curl = base_url + query_url + SID + query_acts #change pagesize to 50
    html = SpiderHandle.get_url(curl)
    return records_num.replace(',','')


def advance_search(query_input,save_dir):
    #basic url
    base_url = 'http://apps.webofknowledge.com/'
    editions = ['SCI', 'SSCI']
    startYear = 1900
    endYear = 2017
    
    #enroll in cookie and get sid
    SpiderHandle = Spider(base_url)
    SID = SpiderHandle.get_sid()
    records_num = query_search(SpiderHandle, SID, query_input, editions, startYear, endYear)
    SpiderHandle.cookie.save('cookie.txt',ignore_discard=True, ignore_expires=True)

    if int(records_num)%50 == 0 :
        pages_num = int(records_num) / 50
    else:
        pages_num = int(records_num) / 50 +1
    
    base_url = 'http://apps.webofknowledge.com'
    query_str = '/summary.do?product=WOS&parentProduct=WOS&search_mode=AdvancedSearch&parentQid=&qid=1&SID='
    base_dir = './Source/'+ save_dir + '/'
    doc_dir = base_dir + str(endYear)
    if os.path.exists(doc_dir) == False:
        os.makedirs(doc_dir)

    for page in range(1, pages_num+1):
        SpiderHandle._get_cookie()
        logging.info("dealing with page "+str(page))
    
        url = base_url + query_str + SpiderHandle.get_sid() + '&&update_back2search_link_param=yes&page=' + str(page)
        html = SpiderHandle.get_url_with_cookie(url)
            
        SpiderHandle.get_all_pages(html)
        SpiderHandle.headers['Referer'] = url

        for curl in SpiderHandle.urls:
            curl = base_url + curl.replace('&amp;','&')
            docid = curl[curl.find('doc=')+4:]
            if docid.find('&') != -1:
                docid = docid[:docid.find('&')]
            logging.info("docid: "+docid)

            html = SpiderHandle.get_url_with_cookie(curl)
            if html == None:
                continue
            f = open(doc_dir+'/'+docid.zfill(5)+'.html','w+')
            f.write(html)
            f.close()
            #time.sleep(1)
        #To avoid Session expired, every 5 pages request for a new session
        if page%5 == 0:
            SpiderHandle = Spider(base_url)
            SID = SpiderHandle.get_sid()
            records_num = query_search(SpiderHandle, SID, query_input, editions, startYear, endYear)
            SpiderHandle.cookie.save('cookie.txt',ignore_discard=True, ignore_expires=True)
    time.sleep(1)

if __name__=="__main__":
    advance_search('TS=({:})'.format(sys.argv[1]),sys.argv[2])
