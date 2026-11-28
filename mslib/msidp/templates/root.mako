<%def name="pre()" filter="trim">
    <div class="header">
        <h1><a href="/">Login</a></h1>
    </div>
</%def>
<%def name="post()" filter="trim">
    <div>
        <div class="footer">
            <p>footer</p>
        </div>
    </div>
</%def>
    ##<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN "
##"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head><title>IDP test login</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
</head>
<body>
    ${pre()}
##        ${comps.dict_to_table(pageargs)}
##        <hr><hr>
${next.body()}
${post()}
</body>
</html>
