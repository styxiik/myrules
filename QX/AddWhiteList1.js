const url = "whitelist1";
const method = "POST";
const headers = {"Field": "test-header-param"};
const data = {"info": "abc"};
const myRequest = {
    url: url,
    method: method, // Optional, default GET.
    headers: headers, // Optional.
    body: JSON.stringify(data) // Optional.
};

$task.fetch(myRequest).then(response => {
    // response.statusCode, response.headers, response.body
    console.log(response.body);
    $notify("白名单", "添加", response.body); // Success!
    $done();
}, reason => {
    // reason.error
    $notify("白名单", "错误", reason.error); // Error!
    $done();
});
