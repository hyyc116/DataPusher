#coding:utf-8

from spider import *
import sys
from bs4 import BeautifulSoup as bs

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
    
    f = open('search_result.html','w')
    f.write(html)
    f.close()

    records_num = re.findall('<a href="/summary.do?(.*?)" title="Click to view the results">(.*?)</a>', html)[0][1]
    print records_num
    
    curl = base_url + query_url + SID + query_acts #change pagesize to 50
    html = SpiderHandle.get_url(curl)
    return records_num.replace(',','')


def advance_search(query_input,save_dir,startYear=1900,endYear=2017,s=2,e=4):
    #basic url
    base_url = 'http://apps.webofknowledge.com/'
    editions = ['SCI', 'SSCI', 'AHCI', 'ISTP', 'ISSHP', 'ESCI', 'CCR', 'IC']
    editions = editions[s:e]
    startYear = startYear
    endYear = endYear
    
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

            #get reference list
            soup = bs(html,'lxml')
            snd_p= soup.select('div.block-text-content p')[1]
            refs= snd_p.select('a[href]')
            if len(refs)==1:
                ref_node = refs[0]
                ref_link = ref_node.get('href')
                ref_count = re.findall(r'(\d+).*',ref_node.get_text().strip())
                logging.info('found {:} references'.format(ref_count[0]))
                ref_url = base_url+"/"+ref_link
                SpiderHandle.headers['Referer'] = curl
                iter_ref_pages(ref_url,SpiderHandle)

            SpiderHandle.headers['Referer'] = url
            time.sleep(1)
        #To avoid Session expired, every 5 pages request for a new session
        if page%5 == 0:
            SpiderHandle = Spider(base_url)
            SID = SpiderHandle.get_sid()
            records_num = query_search(SpiderHandle, SID, query_input, editions, startYear, endYear)
            SpiderHandle.cookie.save('cookie.txt',ignore_discard=True, ignore_expires=True)
    time.sleep(1)


def iter_ref_pages(ref_url,handler,base_url):
    page_num=1
    html = handler.get_url_with_cookie(ref_url)
    links = handler.return_all_pages(html)
    open('test-ref-{:}.html'.format(page_num),'w').write(html)
    logging.info('Ref page {:} found {:} links'.format(page_num,len(links)))
    soup = bs(html,'lxml')
    nextPage = soup.select('a.paginationNext')[0]
    next_url = nextPage.get('href')
    while next_url !='javascript: void(0)':
        page_num+=1
        html = handler.get_url_with_cookie(next_url)
        open('test-ref-{:}.html'.format(page_num),'w').write(html)
        links = handler.return_all_pages(html)
        for i,link in enumerate(links):
            logging.info("dealing {:} reference paper.".format(i))
            ref_paper_link=base_url+"/"+link
            ref_html = handler.get_url_with_cookie(ref_paper_link)
            open('ref_paper_{:}.html'.format(i),"w").write(ref_html)
        logging.info('Ref page {:} found {:} links'.format(page_num,len(links)))
        soup = bs(html,'lxml')
        nextPage = soup.select('a.paginationNext')[0]
        next_url = nextPage.get('href')



if __name__=="__main__":
    advance_search('TS=({:})'.format(sys.argv[1]),sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]))
