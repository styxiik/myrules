    /**
     * @fileoverview Example to compose HTTP request
     * and handle the response.
     *
     */

    const list = ["addwhite1", "addwhite2"];
    const method = "POST";
    const headers = {"Field": "test-header-param"};
    const data = {"info": "abc"};

    for (const url of list) {
        const myRequest = {
            url: url,
            method: method, // Optional, default GET.
            headers: headers, // Optional.
            body: JSON.stringify(data) // Optional.
        };
        $task.fetch(myRequest).then(response => {
            // response.statusCode, response.headers, response.body
            console.log(response.body);
            $notify("成功", "~", response.body); // Success!
            $done();
        }, reason => {
            // reason.error
            $notify("失败", "！", reason.error); // Error!
            $done();
    })};
