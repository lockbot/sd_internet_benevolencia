function main(splash)
    splash:init_cookies(splash.args.cookies)
    assert(splash:go(splash.args.url))
    splash:wait(3.5)
    return {
        cookies = splash: get_cookies(),
    }
end