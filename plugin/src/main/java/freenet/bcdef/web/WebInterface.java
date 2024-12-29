/**
 * Manage the web interface.
 */
package freenet.bcdef.web;

import freenet.bcdef.App;
import freenet.client.HighLevelSimpleClient;
import freenet.clients.http.PageMaker;
import freenet.clients.http.ToadletContainer;
import freenet.clients.http.Toadlet;

public class WebInterface {
	private final App app;
	private PageMaker pageMaker;
	private final ToadletContainer toadletContainer;
	private final HighLevelSimpleClient client;
	private final String NAVIGATION_CATEGORY = "bcdef";

	private HelloPageToadlet hello;
	private Toadlet rest;

	public WebInterface(App a, HighLevelSimpleClient client, ToadletContainer container, PageMaker pageMaker) {
		app = a;
		toadletContainer = container;
		this.client = client;
		this.pageMaker = pageMaker;
	}

	public void load() {
		pageMaker.addNavigationCategory("/bcdef/hello", NAVIGATION_CATEGORY, "BCDEF", app);
		
		hello = new HelloPageToadlet(client, app);
		toadletContainer.register(hello, NAVIGATION_CATEGORY, "/bcdef/hello", true, "Hello", "Hello", true, null);
		rest = new RestToadlet(client, app);
		toadletContainer.register(rest, NAVIGATION_CATEGORY, rest.path(), false, "Rest", "Rest", true, null);
	}

	public void unload() {
		toadletContainer.unregister(hello);
		pageMaker.removeNavigationCategory(NAVIGATION_CATEGORY);
	}
}
