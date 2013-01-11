package be.ugent.zeus.hydra;

import android.os.Bundle;
import android.util.Log;
import android.webkit.WebView;
import android.widget.TextView;
import be.ugent.zeus.hydra.data.rss.Item;
import com.actionbarsherlock.app.SherlockActivity;
import java.text.SimpleDateFormat;

/**
 * TODO: implement this properly as a fragment, so we can display this a lot cleaner on tablets (running 4.0+,
 * i think)
 *
 * @author Thomas Meire
 */
public class SchamperDailyItem extends SherlockActivity {

	@Override
	public void onCreate(Bundle icicle) {
		super.onCreate(icicle);
		setContentView(R.layout.schamper_item);

		Item item = (Item) getIntent().getSerializableExtra("item");


		String date = String.format(new SimpleDateFormat("dd MMM yyyy hh:mm").format(item.pubDate));

		String html =
			   "<body>"
			 + "	<header><h1>" + item.title + "</h1><p class='meta'>" + date + "<br />door " + item.creator + "</div></header>"
			 + "	<div class='content'>" + item.description + "</div>"
			 + "</body>";

		WebView content = (WebView) findViewById(R.id.schamper_item);
		String withCss = "<link rel=\"stylesheet\" type=\"text/css\" href=\"schamper.css\" />" + html;
		content.loadDataWithBaseURL("file:///android_asset/", withCss, "text/html", "UTF-8", null);
	}
}
