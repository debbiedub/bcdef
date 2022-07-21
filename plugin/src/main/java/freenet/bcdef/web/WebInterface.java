/**
 * Manage the web interface.
 */
package freenet.bcdef.web;

import freenet.bcdef.App;
import freenet.client.HighLevelSimpleClient;
import freenet.clients.http.PageMaker;
import freenet.clients.http.ToadletContainer;

public class WebInterface {
	private final App app;
	private PageMaker pageMaker;
	private final ToadletContainer toadletContainer;
	private final HighLevelSimpleClient client;
	private final String NAVIGATION_CATEGORY = "nav";

	private HelloPageToadlet hello;

	public WebInterface(App a, HighLevelSimpleClient client, ToadletContainer container, PageMaker pageMaker) {
		app = a;
		toadletContainer = container;
		this.client = client;
		this.pageMaker = pageMaker;
	}

	public void load() {
		pageMaker.addNavigationCategory("/bcdef/", NAVIGATION_CATEGORY, "BCDEF", app);
		
		hello = new HelloPageToadlet(client, app);
		toadletContainer.register(hello, NAVIGATION_CATEGORY, "/bcdef/hello", true, "Hello", "BCDEF Hello", true, null);
	}

	public void unload() {
		toadletContainer.unregister(hello);
		pageMaker.removeNavigationCategory(NAVIGATION_CATEGORY);
	}
}
