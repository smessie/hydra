package be.ugent.zeus.resto.client.util;

import android.util.Log;
import be.ugent.zeus.resto.client.data.Activity;
import java.io.StringReader;
import java.util.LinkedList;
import java.util.List;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

/**
 * Parse the activity-xml into a list of activities. The activities are not
 * yet grouped by date!
 * 
 * @author Thomas Meire
 */
public class ActivityXmlParser {

  public List<Activity> parse(String activityXML) {
    DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();

    List<Activity> list = new LinkedList<Activity>();

    try {
      Document doc = dbf.newDocumentBuilder().parse(new InputSource(new StringReader(activityXML)));
      doc.getDomConfig().setParameter("cdata-sections", false);

      Node clubNode = doc.getFirstChild();
      NodeList activityList = clubNode.getChildNodes();
      int len = activityList.getLength();

      for (int i = 0; i < len; i++) {
        list.add(parse(activityList.item(i)));
      }
    } catch (Exception e) {
      Log.w("[ActivityXmlParser", "Something went wrong while parsing the activity xml!", e);
    }
    return list;
  }

  private Activity parse(Node node) {
    Activity activity = new Activity();

    activity.date = node.getAttributes().getNamedItem("date").getTextContent();
    // TODO parse the other attributes (date, to, from, association)
    
    NodeList children = node.getChildNodes();
    for (int i = 0; i < children.getLength(); i++) {
      Node child = children.item(i);

      if ("title".equals(child.getNodeName())) {
        activity.title = child.getTextContent();
        // FIXME: cutoff the CDATA tags
        activity.title = activity.title.substring(9, activity.title.length() - 3);
      } else if ("location".equals(child.getNodeName())) {
        activity.location = child.getTextContent();
        // FIXME: cutoff the CDATA tags
        activity.location = activity.location.substring(9, activity.location.length() - 3);
      } else {
        // unknown tag, ignore
      }
    }

    return activity;
  }
}