<%inherit file="root.mako"/>

<h1>Please log in</h1>
<p class="description">
    To register it's quite simple: enter a valid username and a password
</p>

<form action="${action|h}" method="post">
    <input type="hidden" name="key" value="${key|h}"/>
    <input type="hidden" name="authn_reference" value="${authn_reference|h}"/>
    <input type="hidden" name="redirect_uri" value="${redirect_uri|h}"/>

    <div class="label">
        <label for="login">Username</label>
    </div>
    <div>
        <input type="text" name="login" value="${login|h}" autofocus><br/>
    </div>

    <div class="label">
        <label for="password">Password</label>
    </div>
    <div>
        <input type="password" name="password"
               value="${password|h}"/>
    </div>

    <input class="submit" type="submit" name="form.submitted" value="Log In"/>
</form>
