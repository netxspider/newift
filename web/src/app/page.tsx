import {HomeExperience} from '@/components/HomeExperience'
import {getHomeStories} from '@/lib/content'

export default async function Home() {
  const stories = await getHomeStories()
  return <HomeExperience stories={stories} />
}
