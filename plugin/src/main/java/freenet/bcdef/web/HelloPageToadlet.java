package freenet.bcdef.web;

import java.io.IOException;
import java.net.URI;

import freenet.bcdef.App;
import freenet.client.HighLevelSimpleClient;
import freenet.clients.http.PageNode;
import freenet.clients.http.RedirectException;
import freenet.clients.http.Toadlet;
import freenet.clients.http.ToadletContext;
import freenet.clients.http.ToadletContextClosedException;
import freenet.support.HTMLNode;
import freenet.support.api.HTTPRequest;

/**
 * The hello page is a simple page with text.
 */
public class HelloPageToadlet extends Toadlet {

	protected HelloPageToadlet(HighLevelSimpleClient client, App app) {
		super(client);
	}

	@Override
	public String path() {
		return "/bcdef/hello";
	}

	public void handleMethodGET(URI uri, final HTTPRequest request, final ToadletContext ctx) 
	throws ToadletContextClosedException, IOException, RedirectException {
		ClassLoader origClassLoader = Thread.currentThread().getContextClassLoader();
		Thread.currentThread().setContextClassLoader(App.class.getClassLoader());
		try {
			PageNode p = ctx.getPageMaker().getPageNode("BCDEF Hello", ctx);
			HTMLNode pageNode = p.outer;
			HTMLNode contentNode = p.content;
			writeContent(request, contentNode);
			writeHTMLReply(ctx, 200, "OK", null, pageNode.generate());
		} finally {
			Thread.currentThread().setContextClassLoader(origClassLoader);
		}
	}

	private void writeContent(HTTPRequest request, HTMLNode contentNode) {
		contentNode.addChild("#", "Hello text.");
		contentNode.addChild("br");
		contentNode.addChild("#", "More text");
		contentNode.addChild("br");
	}
}
