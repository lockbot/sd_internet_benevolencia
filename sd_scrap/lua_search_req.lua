function main(splash)
    splash:init_cookies(splash.args.cookies)
    splash:go(splash.args.url)
    splash:runjs("document.querySelector('#termo').value = '$#busca#$'")
    splash:runjs("document.querySelector('#btn-tipo-ato').click()")
    splash:runjs("document.getElementsByClassName('form-check-label')[1].click()")
    splash:wait(1.5)
    local num = assert(splash:evaljs("document.getElementsByClassName('pb-2')[0].innerText"))
    splash:wait(0.5)
    return {
        num = num,
    }
end