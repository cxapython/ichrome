import json
import re

from ichrome import Chrome, ChromeDaemon, logger
"""
Test normal usage of ichrome.

1. use `with` context for launching ChromeDaemon daemon process.
2. init Chrome for connecting with chrome background server.
3. Tab ops:
  3.1 create a new tab
  3.2 goto new url with tab.set_url, and will stop load for timeout.
  3.3 get cookies from url
  3.4 inject the jQuery lib by a static url.
  3.5 auto click ok from the alert dialog.
  3.6 remove `href` from the third `a` tag, which is selected by css path.
  3.7 remove all `href` from the `a` tag, which is selected by css path.
  3.8 use querySelectorAll to get the elements.
  3.9 Network crawling from the background ajax request.
  3.10 click some element by tab.click with css selector.
  3.11 show html source code of the tab
"""


def test_example():
    """Example for crawling a special background request."""

    # reset default logger level, such as DEBUG
    # import logging
    # logger.setLevel(logging.INFO)
    # launch the Chrome process and daemon process, will auto shutdown by 'with' expression.
    def on_startup(chromed):
        chromed.started = 1

    def on_shutdown(chromed):
        chromed.__class__.bye = 1

    with ChromeDaemon(host="127.0.0.1",
                      port=9222,
                      max_deaths=1,
                      on_startup=on_startup,
                      on_shutdown=on_shutdown) as chromed:
        assert chromed.started
        logger.info(chromed)
        # create connection to Chrome Devtools
        chrome = Chrome(host="127.0.0.1", port=9222, timeout=3, retry=1)
        # now create a new tab without url
        tab = chrome.new_tab()
        # add a default callback
        test_cache = []
        tab._default_recv_callback.append(
            lambda tab, data: test_cache.append(data))
        # reset the url to bing.com, if loading time more than 5 seconds, will stop loading.
        # if inject js success, will alert Vue
        tab.set_url("https://www.bing.com/",
                    referrer="https://www.github.com/",
                    timeout=5)
        assert 'bing' in tab.url, tab.url
        assert test_cache, test_cache
        test_cache.clear()
        tab._default_recv_callback.clear()
        logger.info(tab.title)
        # get_cookies from url
        logger.info(tab.get_cookies("http://cn.bing.com"))
        # test inject_js, if success, will alert jQuery version info 3.3.1
        logger.info(
            tab.inject_js(
                "https://cdn.staticfile.org/jquery/3.3.1/jquery.min.js"))
        logger.info(
            tab.js("alert('jQuery inject success:' + jQuery.fn.jquery)"))
        assert not test_cache, test_cache
        tab.js(
            'alert("Check the links above disabled, and then input `test` to the input position.")'
        )
        # automate press accept for alert~
        tab.send("Page.handleJavaScriptDialog", accept=True)
        # remove href of the a tag.
        tab.click("#sc_hdu>li>a", index=3, action="removeAttribute('href')")
        # remove href of all the 'a' tag.
        tab.querySelectorAll("#sc_hdu>li>a",
                             index=None,
                             action="removeAttribute('href')")
        # use querySelectorAll to get the elements.
        for i in tab.querySelectorAll("#sc_hdu>li"):
            logger.info("Tag: %s, id:%s, class:%s, text:%s" %
                        (i, i.get("id"), i.get("class"), i.text))
        # enable the Network function, otherwise will not recv Network request/response.
        logger.info(tab.send("Network.enable"))
        # here will block until input string "test" in the input position.
        # tab is waiting for the event Network.responseReceived which accord with the given filter_function.
        recv_string = tab.wait_event(
            "Network.responseReceived",
            filter_function=lambda r: re.search(r"&\w+=test", r or ""),
            wait_seconds=None,
        )
        # now catching the "Network.responseReceived" event string, load the json.
        recv_string = json.loads(recv_string)
        # get the requestId to fetch its response body.
        request_id = recv_string["params"]["requestId"]
        logger.info("requestId: %s" % request_id)
        # send request for getResponseBody
        resp = tab.send("Network.getResponseBody",
                        requestId=request_id,
                        timeout=5)
        # now resp is the response body result.
        logger.info("getResponseBody success %s" % resp)
        # directly click the button matched the cssselector #sb_form_go, here is the submit button.
        logger.info(tab.click("#sb_form_go"))
        tab.wait_loading(3)
        # show some html source code of the tab
        logger.info(tab.html[:100])
        tab.send('Browser.close')
        # # now click close button of the chrome browser.
        # chromed.run_forever()
    assert ChromeDaemon.bye


if __name__ == "__main__":
    test_example()
