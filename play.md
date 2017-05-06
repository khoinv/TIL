### Router reserve: routes.Applications.hello("Bob")
### BodyParser
- Body: BodyParser[A] => iteratee[Array[Byte], String] => read data by chunk

```scala
trait Action[A] extends (Request[A] => Result) {
  def parser: BodyParser[A]
}
```
### Action Composition

- Custom Action

```Scala
LoggingAction extends ActionBuilder[Request]{
  def invokeBlock[A](request: Request[A], block: (Request[A]) => Future[Result]) = {
    Logger.info("Calling action")
    block(request)
  }
}
```

- Action Composition

```Scala
case class Logging[A](action: Action[A]) extends Action[A]{

  def apply(request: Request[A]): Future[Result] = {
    Logger.info()
    action(request)
  }

  lazy val parser = action.parser
}

object LoggingAction extends ActionBuilder[Request]{
  def invokeblock[A](request: Request[A], block: (Request[A]) => Future[Result]){
    block(request)

    override def composeAction[A](action: Action[A]) = new Logging(action)
  }
}
```

- use:

```Scala
def index = LoggingAction{
  Ok("Hello world")
}
```

or

```Scala
def index = Logging {
  Action{
    Ok("Hello world")
  }
}
```

```Scala
def onlyHttps[A](action: Action[A]) = Action.async(action.parser) { request =>
  request.headers.get("X-Forwarded-Proto").collect {
    case "https" => action(request)
    } getOrElse{
      Future.successful(Forbidden("Ony https requests allowed"))
    }
}
```

- Difference request type
- Authenticate

```Scala
class UserRequest[A](val username: Option[String], request: Request[A]) extends WrappedRequest[A](request)

object UserAction extends ActionBuilder[UserRequest] with ActionTransformer[Request, UserRequest]{
  def transform[A](request: Request[A]) = Future.successful {
    new UserRequest(request.session.get("username"), request)
  }
}
```

- Adding information to requests
```Scala
class ItemRequest[A](val item: Item, request: UserRequest) extends WrappedRequest[A](request){
  def username = request.username
}

def ItemAction(itemId: String) = new ActionRefiner[UserRequest, ItemRequest] {
  def refine[A](input: UserRequest[A]) = Future.successful {
    ItemDao.findById(itemId)
      .map(new ItemRequest(_, input))
      .toRight(NotFound)
  }
}

```

- Validate Request
```Scala
object PermissionCheckAction extends ActionFilter[ItemRequest] {
  def filter[A](input: ItemRequest[A]) = Future.successful {
    if(!input.item.accessibleByUser(input.username))
      Some(Forbidden)
    else
      None
  }
}
```

- Putting it all together
```Scala
def tagItem(itemId: String, tag: String) =
  (UserAction andThen ItemAction(itemId) andThen PermissionCheckAction) { request =>
    request.item.addTag(tag)
    Ok("User " + request.username + " taged " + request.item.id)
  }
// Play also provides a global filter API
```

### Content

```Scala
val list = Action { request =>
  val items = Item.findAll
  render {
    case Accepts.Html() => Ok(views.html.list(items))
    case Accepts.Json() => Ok(Json.toJson(items))
  }
}
```

### Request extractors

```Scala
val AcceptsMp3 = Accepting("audio/mp3")
render {
  case AcceptsMp3 => ???
}
```

### Handing error
- Client Error
- Server Error
* if the action code throw an exception, Play will catch this and generate a server error page to send to the client
-> define new error handler

```Scala
class ErrorHandler extends HttpErrorHandler {
  def onClientError(request: RequestHeader, statusCode: Int, message: String) = {
    Future.successful {
      Status(statusCode)("A client error occurred: " + message)
    }
  }
}
```

* Config error handle in application.cof
play.http.errorHanlder

### Handling asynchronous results

- execute context will offen be equivalent to a thead pool, though not necessarily
- Cannot turn synchronous IO into asynchronous by warraping it in a Future => it is necessarily configure it to run in a reparate excution context
- It can helpful to use Actors for non-bloking operators. Actor provice a clean model for handling timeouts and failures, setting up bloking excution contexts and managing any state that may be associated with the service
- Also Actor provide patterns like ScatterGatherFirstCompletedRouter to address simultanceous cache or database requests and allow remote excution on cluster of backend servers
- Actions are asynchronous by default
- There is a single kind of Action
- Handling time-outs

```Scala
def index = Action.async { request =>
  val futureInt = scala.concurrent.Future { insentiveComputation() }
  val timeoutFuture = play.api.libs.concurrent.Promise.timeout("Oops", 1.seconds)
  Future.firstOfCompleteOf(Seq(futureInt, timeutFuture)).map {
    case i: Int => Ok("Got result: " + i)
    case t: String => InternalServerError(t)
  }
}
```

- Streaming Https response
  + int http1.1 => keep a single connection open to serve serveral Http request and reqponses, the server must send the appropriate Content-Length Http header along with the response
  + Default you a not specicifying Content-Length header when send back a simple result. Of course, because the content you are sending is well-known, Play will compute the content size for you and to generate appropriate header
  + Result body is specified using a play.api.libs.iteratee.Enumerator

```Scala
def index = Action {
  Result {
    header = ResponseHeader(200),
    body = Enumerator("Hello World")
  }
}
```

=> This mean that to compute the Content-Length header properly, Play must consume the whole enumerator and load its content in to memory
- Sending large amounts of data

```Scala
def index = Action {
  val file = new java.io.File("/tmp/fileToServe.pdf")
  val fileContent: Enumerator[Array[Byte]] = Enumerator.fromFile(file)

  Result{
    header = ResponseHeader(200, Map(CONTENT_LENGTH -> file.length.toString)), // if CONTENT_LENGTH is not specified, all of file content will be loaded into memory to comsume CONTENT_LENGTH
    body = fileContent
  }
}
```

- Serving file
easy helpers for common task of serving a local file
```Scala
def index = {
  Ok.sendFile(new java.io.File("tmp/fileToServe.pdf"))
}
```

- Content-Disposition: specify how the web browser should handle this response. The default downloading this file, set header Content-Disposition:attachment; filename=fileToServe.pdf to the http response
  + if you want to serve this file inline:
  ```Scala
  def index = {
    Ok.sendfile(
      content = new java.io.File("/tmp/fileToServe.pdf")
      inline = true
    )
  }
  ```

  + Chunked Response
  with no content-size availabel?
    - using Chunked tranfer encoding
      - size of each chunk is sent right before the chunk itself, so that a client can tell when it has finished receiving data for that chunk. Data transfer is terminated by a final chunk of length zero
      - can serve the data live, meaning that we send chinks of data as soon as thay are available
      - the drawback is that since the web browser doesn't know the content size, it is not able display a proper download progess bar

      ```Scala
      def index = {
        val data = getDataStream
        val dataContent: Enumerator[Array[Byte]] = Enumerator.fromStream(data)
        Ok.chunked(dataContent)
      }

      def index = {
        Ok.chunked(
          Enumerator("kiki", "foo", "bar").andThen(Enumerator.eof)
        )
      }

      We can inspect the HTTP response sent by the server:
      HTTP/1.1 200 OK
      Content-Type: text/plain; charset=utf-8 Transfer-Encoding: chunked
      4
      kiki
      3
      foo
      3
      bar
      0
      ```
### Comet Socket
- Using chunked responses to create Comet Sockets

```Scala
val toCometMessage = Enumeratee.map[String]{ data =>
  Html("""<script>console.log('""" + data + """')</script>""")
}

def comet = Action {
  val events = Enumerator("kiki", "foo", "bar")
  Ok.chunked(events &> toCometMessage) // &> = events.through(toCometMessage)
}
```

- Using the play.api.libs.Comet helper
  + support String, Json messages. It can also be extended via type classes to support more message types

  ```Scala
  def commet = Action {
    val events = Enumerator("kiki", "for", "bar")
    Ok.chunked(event &> Comet(callback = "console.log"))
  }
  ```

### Websocket
- Using actor
- Using Iteratee
1. Using actor

```Scala
def socket = WebSocket.acceptWithActor[String, String](request => out =>
    MyWebSocketActor.props(out)
    )

object MyWebSocketActor {
  def props(out: ActorRef) = Props( new MyWebSocketActor(out))
}

class MyWebSocketActor(out: ActorRef) extends Actor {
  def receive = {
    case msg: String =>
      out ! ("I receive yout message: " + msg)
  }
}
```

- Detecting when a WebSocket has closed
```Scala
override def postStop() = {
  someResource.close()
}
```

- Close a WebSocket
self ! PoisonPill
- Reject a WebSocket

```Scala
def socket = WebSocket.tryAcceptWithActor[String, String]{ request =>
  Future.successful(request.session.get("user") match {
    case None => Left(Forbiden)
    case Some(_) => Right(MyWebSocketActor.props)
  })
}
```
- Handing differnce type of messages
  - So far we have only seen handling String frames. Play also has built in handlers for Array[Byte] frames, and JsValue messages parsed from String frames. You can pass these as the type parameters to the WebSocket creation method, for example

```Scala
def socket = WebSocket.acceptWithActor[JsValue, JsValue] { request => out =>
  MyWebSocketActor.props(out)
}
```

```Scala
implicit val inEventFormat = Json.format[InEvent]
implicit val outEventFormat = Json.fromat[OutEvent]
implicit val inEventFrameFormatter = FrameFormatter.jsonFrame[InEvent]
implicit val outEventFormatter = FrameFromatter.jsonFrame[OutEvent]

def socket =  WebSocket.acceptWithActor[InEvent, OutEvent] { request => out =>
  MyWebSocketActor.props(out)
}
```

2. Handing WebSocket with iteratee
* While Actor are better abstraction for handling discrete messages, iteratees are ofen a better abstraction for handling streams.
To handle a WebSocket request, use a WebSocket instead of Action:

```Scala
def socket = WebSocket.using[String]{ request =>
  // log events to the console
  val in = Iteratee.foreach[String](println).map { _ =>
    println("Disconnected")
  }

  // Send a single "Hello!" message
  val out = Enumerator("Hello!")

  (in, out)
}
```

* A WebSocket has access to the request headers(from the HTTP request that initaties the WebSocket connection), allowing you to retrieve standard headers and session data. However, it doesn't have access to a request body, nor to the HTTP response.

- When constructing a WebSocket this way, we must return both in and out channels.
  1. in channel is an Iteratee[A, Unit], that willbe notified for each message, and will receive EOF when the socket is closed on the client side.
  2. out chanel is an Enumerator[A] that will generate the messages to be sent to the Web client. It can close the connection on the server side by sending EOF

Let write another example that discards the input data and closes the socket after sending "Hello!" message

```Scala
def socket = WebSocket.using[String]{ request =>
  val in = Iteratee.ignore[String]

  val out = Enumerator("Hello!").andThen(Enumerator.eof)
}
```

- Another example in which the input data id logged to standard out and broadcast to the client utilizing Concurrent.broadcast

```Scala
def socket = WebSocket.using[String] { request =>
  // Concurrent.broadcast returns (Enumerator, Concurrent.chanel)
  val (out, chanel) = Concurrent.broadcast[String]

  // Log the message to stdout and send response back to client
  val in = Interatee.foreach[String] {
    msg =>
      println(msg)
      // the Enumerator returned by Concurrent.broadcast subscribes to the chanel and will
      // receive the pushed messages
      chanel push ("I received your message:" + msg)
  }
  (in, out)
}
```

### Protect against Cross Site Request Forgery
* an attacker can coerce a victims browser to make the following types of request
- All GET requests
- POST requests with bodies of type application/x-www-form-urlencoded, multipart/form-data and text/plain

* attacker can not:
- coerce the browser to use other request methods such as PUT and DELETE
- coerce the browser to post other content types, such as application/json
- coerce the browser to send new coockies, other than those that server has already set
- coerce the browser to set arbitrary headers, other than the normal headers the browser adds to request

=> Since GET request are not meant to be mutative, there is no danger to an application that follows this best practice. So the only requests that need CSRF protection are POSTrequest with the above mentioned content types.
* Play's CSRF protection
- Using CSRF token. This token get placed either in the query string or body of every form submitted, and also gets placed in the users session. Play then verifies, that both tokens are present and match.
- Simple to protection for non browser requests, such as requests made through AJAX, Play also support the following:
  + If an X-Requested-With header is present, Play will consider the request safe. X-Requested-With is add to requests by many popular Javascript libraries, such as JQuery
  + If a Csrf-Token header with value nocheck is present, or with a vaid CSRF, Play will consider the request safe

### Play WS API
- Calling get() or post() will case the body of the request to loaded into memory befor the response is made available. When you are downloading with large, multi-gagibyte files, this may result in unwelcome garbage collection or event ot of memory errors.

WS lets you use the response incrementally by using an iteratee. The stream() and getStream() methods on WSRequest return Future[(WSResponseHeaders, Enumerator[Array[Byte]])]. The enumerator contains the response body.
```Scala
// make the request
// simple count the number of bytes returned by the response
val futureResponse: Future[(WSResponseHeaders, Enumerator[Array[Byte]])] =
  ws.url(url).getStream()

val bytesReturned: Future[File] = futureResponse.flatMap {
  case (headers, body) =>
    // Count the number of bytes returned
    body |>> Iteratee.fold(01){ (total, bytes) =>
      total + bytes.length
    }
}


// make the request
// Of course, usually you won't want to consume large bodies like this, the more common use case is to stream the body out to another location.
// Example, to stream the body to a file:
val futureResponse: Future[(WSResponseHeaders, Enumerator[Array[Byte]])] =
  ws.url(url).getStream()

val downloadFile: Future[File] = futureResponse.flatMap{
  case (headers, body) =>
    val outputStream = new FileOutputStream(file)
    // The iteratee that writes to the output stream
    val iteratee = Iteratee.foreach[Array[Byte]] { bytes =>
      outputStream.write(bytes)

      // Feed the body into the iteratee
      (body |>> iteratee).andThen {
        case result =>
          // Close the output stream whether there was an error or not
          outputSteam.close()
          result.get
      }.map(_ => file)
    }
}


// Another common destination for response bodies is to stream them through to a response that this server is currently serving:
def downloadFile = Action.async{

  // Make the request
  ws.url(url).getStream().map {
    case (response, body) =>
      // Check the response was successful
      if(response.status == 200) {
        val contentType = response.headers.get("Content-Type").flatMap(_.headOption)
          .getOrElse("application/octet-stream")
          // If there's a content length, send that, otherwise return the body chunked
          response.headers.get("Content-Length") match {
            case Some(Seq(length)) =>
              Ok.feed(body).as(contentType).withHeader("Content-Length" -> length)
            case _ =>
              Ok.chunked(body).as(contentType)
          }
          } else {
            BadGateway
          }
  }
}
```


- Directing the body elsewhere

```Scala
def forward(request: WSRequest): BodyParser[WSResponse] = BodyParser{ req =>
  Accumulator.source[ByteString].mapFuture { resource =>
    request
    // TODO: stream body when support is implemented
    // .withBody(source)
      .execute()
      .map(Right.apply)
  }
}

def myAction = Action(forward(ws.url("https://example.com"))) { req =>
  Ok("Uploaded")
}
```

- Custom parsing using Akka Stream
+ parse CSV file
ref: https://www.playframework.com/documentation/2.5.x/ScalaBodyParsers#directing-the-body-elsewhere
ref: https://groups.google.com/forum/#!topic/play-framework/zgTgfoEvnFc
